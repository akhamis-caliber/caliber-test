"""
Enhanced normalization with proper metric direction handling
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class EnhancedNormalizer:
    """Enhanced normalization with metric direction awareness"""
    
    def __init__(self):
        # Higher is better metrics (as per document)
        self.higher_is_better = [
            'ctr', 'conversion_rate', 'completion_rate', 'ias_display_fully_in_view_1s',
            'sampled_in_view', 'player_completion', 'tv_quality_index_ratio', 'unique_id_ratio'
        ]
        
        # Lower is better metrics (as per document)
        self.lower_is_better = [
            'cpm', 'ecpm', 'ad_load_rate', 'ad_refresh_rate', 'player_errors', 'player_mute'
        ]
    
    def normalize_campaign_metrics(self, df: pd.DataFrame, source: str, channel: str, 
                                 goal: str, ctr_sensitive: bool = False) -> Tuple[pd.DataFrame, Dict]:
        """
        Normalize campaign metrics with proper direction handling
        
        Args:
            df: Input DataFrame
            source: Data source ('TTD' or 'PulsePoint')
            channel: Channel type
            goal: Campaign goal ('Awareness' or 'Action')
            ctr_sensitive: Whether CTR sensitivity applies
            
        Returns:
            Tuple of (normalized_dataframe, normalization_summary)
        """
        logger.info(f"Starting enhanced normalization for {source} {channel} {goal}")
        
        df_norm = df.copy()
        normalization_params = {}
        
        # Get metrics to normalize based on source/channel/goal
        metrics_to_normalize = self._get_metrics_for_normalization(source, channel, goal, ctr_sensitive)
        
        # Normalize each metric
        for metric in metrics_to_normalize:
            if metric in df_norm.columns:
                normalized, params = self._normalize_metric(df_norm[metric], metric)
                df_norm[f'{metric}_normalized'] = normalized
                normalization_params[metric] = params
                
                logger.info(f"Normalized '{metric}' using {params['method']} method")
        
        # Create score-ready features
        df_norm, feature_columns = self._create_score_ready_features(df_norm, source, channel)
        
        # Create summary
        summary = {
            'source': source,
            'channel': channel,
            'goal': goal,
            'ctr_sensitive': ctr_sensitive,
            'normalized_columns': list(normalization_params.keys()),
            'parameters': normalization_params,
            'feature_columns': feature_columns,
            'rows_processed': len(df_norm),
            'metric_directions': self._get_metric_directions(metrics_to_normalize)
        }
        
        logger.info(f"Enhanced normalization completed: {len(feature_columns)} features created")
        return df_norm, summary
    
    def _get_metrics_for_normalization(self, source: str, channel: str, goal: str, 
                                     ctr_sensitive: bool) -> List[str]:
        """Get list of metrics to normalize based on configuration"""
        if source == 'TTD':
            if channel == 'display':
                if goal == 'Awareness':
                    if ctr_sensitive:
                        return ['cpm', 'ias_display_fully_in_view_1s', 'ctr', 'ad_load_rate', 'ad_refresh_rate']
                    else:
                        return ['cpm', 'ias_display_fully_in_view_1s', 'ad_load_rate', 'ad_refresh_rate']
                else:  # Action
                    return ['cpm', 'ias_display_fully_in_view_1s', 'conversion_rate', 'ctr', 'ad_load_rate', 'ad_refresh_rate']
            
            elif channel in ['video', 'audio', 'video_mobile']:
                return ['cpm', 'sampled_in_view', 'player_completion', 'player_errors', 'player_mute']
            
            elif channel == 'ctv':
                return ['tv_quality_index_ratio', 'unique_id_ratio']
        
        elif source == 'PulsePoint':
            if channel == 'display':
                if goal == 'Awareness':
                    return ['ecpm', 'ctr', 'conversion_rate']
                else:  # Action
                    return ['ecpm', 'ctr', 'conversion_rate']
            
            elif channel == 'video':
                return ['ecpm', 'ctr', 'completion_rate', 'conversion_rate']
        
        # Default fallback - return all available metrics
        return ['ctr', 'cpm', 'conversion_rate', 'sampled_in_view', 'player_completion', 'player_errors', 'player_mute']
    
    def _normalize_metric(self, series: pd.Series, metric_name: str) -> Tuple[pd.Series, Dict]:
        """
        Normalize a single metric with proper direction handling
        
        Args:
            series: Input series
            metric_name: Name of the metric
            
        Returns:
            Tuple of (normalized_series, normalization_params)
        """
        # Handle edge case where all values are the same
        if series.nunique() <= 1:
            logger.warning(f"All values in {metric_name} are the same ({series.iloc[0]}), returning zeros")
            normalized = pd.Series(np.zeros(len(series)), index=series.index)
            params = {
                'method': 'uniform',
                'metric': metric_name,
                'direction': self._get_metric_direction(metric_name),
                'all_same': True,
                'value': float(series.iloc[0])
            }
            return normalized, params
        
        # Determine if metric should be inverted
        should_invert = metric_name in self.lower_is_better
        
        # Min-max normalization to 0-1 range
        min_val = series.min()
        max_val = series.max()
        
        if should_invert:
            # For lower-is-better metrics, invert the normalization
            normalized = (max_val - series) / (max_val - min_val)
            method = 'min_max_inverted'
        else:
            # For higher-is-better metrics, standard normalization
            normalized = (series - min_val) / (max_val - min_val)
            method = 'min_max'
        
        # Handle NaN values
        normalized = normalized.fillna(0)
        
        params = {
            'method': method,
            'metric': metric_name,
            'direction': self._get_metric_direction(metric_name),
            'original_min': float(min_val),
            'original_max': float(max_val),
            'inverted': should_invert,
            'all_same': False
        }
        
        return normalized, params
    
    def _get_metric_direction(self, metric_name: str) -> str:
        """Get whether metric is higher-is-better or lower-is-better"""
        if metric_name in self.higher_is_better:
            return 'higher'
        elif metric_name in self.lower_is_better:
            return 'lower'
        else:
            # Default to higher-is-better for unknown metrics
            return 'higher'
    
    def _create_score_ready_features(self, df: pd.DataFrame, source: str, channel: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Create final score-ready features
        
        Args:
            df: DataFrame with normalized columns
            source: Data source
            channel: Channel type
            
        Returns:
            Tuple of (dataframe, list_of_feature_columns)
        """
        df_features = df.copy()
        feature_columns = []
        
        # Map normalized columns to score-ready features
        metric_mappings = {
            'ctr_normalized': 'ctr_score_ready',
            'cpm_normalized': 'cpm_score_ready',
            'ecpm_normalized': 'ecpm_score_ready',
            'conversion_rate_normalized': 'conversion_rate_score_ready',
            'completion_rate_normalized': 'completion_rate_score_ready',
            'ias_display_fully_in_view_1s_normalized': 'ias_display_fully_in_view_1s_score_ready',
            'ad_load_rate_normalized': 'ad_load_rate_score_ready',
            'ad_refresh_rate_normalized': 'ad_refresh_rate_score_ready',
            'sampled_in_view_normalized': 'sampled_in_view_score_ready',
            'player_completion_normalized': 'player_completion_score_ready',
            'player_errors_normalized': 'player_errors_score_ready',
            'player_mute_normalized': 'player_mute_score_ready',
            'tv_quality_index_ratio_normalized': 'tv_quality_index_ratio_score_ready',
            'unique_id_ratio_normalized': 'unique_id_ratio_score_ready'
        }
        
        # Create score-ready features
        for normalized_col, score_ready_col in metric_mappings.items():
            if normalized_col in df_features.columns:
                df_features[score_ready_col] = df_features[normalized_col].fillna(0)
                feature_columns.append(score_ready_col)
                logger.info(f"Created {score_ready_col} from {normalized_col}")
            else:
                logger.warning(f"Normalized column {normalized_col} not found in dataframe")
        
        # Handle case where we have raw metrics but no normalized versions
        # This is a fallback for when normalization didn't create the expected columns
        fallback_mappings = {
            'ctr': 'ctr_score_ready',
            'cpm': 'cpm_score_ready',
            'ecpm': 'ecpm_score_ready',
            'conversion_rate': 'conversion_rate_score_ready',
            'completion_rate': 'completion_rate_score_ready',
            'ias_display_fully_in_view_1s': 'ias_display_fully_in_view_1s_score_ready',
            'ad_load_rate': 'ad_load_rate_score_ready',
            'ad_refresh_rate': 'ad_refresh_rate_score_ready',
            'sampled_in_view': 'sampled_in_view_score_ready',
            'player_completion': 'player_completion_score_ready',
            'player_errors': 'player_errors_score_ready',
            'player_mute': 'player_mute_score_ready'
        }
        
        for raw_col, score_ready_col in fallback_mappings.items():
            if raw_col in df_features.columns and score_ready_col not in feature_columns:
                # Create a simple normalization for the raw metric
                raw_values = df_features[raw_col].fillna(0)
                if raw_values.max() != raw_values.min():
                    normalized_values = (raw_values - raw_values.min()) / (raw_values.max() - raw_values.min())
                else:
                    normalized_values = pd.Series([0.5] * len(raw_values), index=raw_values.index)
                
                df_features[score_ready_col] = normalized_values
                feature_columns.append(score_ready_col)
                logger.info(f"Created fallback {score_ready_col} from raw {raw_col}")
        
        logger.info(f"Created {len(feature_columns)} score-ready features: {feature_columns}")
        return df_features, feature_columns
    
    def _get_metric_directions(self, metrics: List[str]) -> Dict[str, str]:
        """Get direction mapping for metrics"""
        return {metric: self._get_metric_direction(metric) for metric in metrics}
    
    def validate_normalization(self, df: pd.DataFrame, feature_columns: List[str]) -> Dict:
        """
        Validate normalization results
        
        Args:
            df: DataFrame with normalized features
            feature_columns: List of feature columns
            
        Returns:
            Validation summary
        """
        validation_results = {}
        
        for col in feature_columns:
            if col in df.columns:
                values = df[col].dropna()
                validation_results[col] = {
                    'min': float(values.min()) if len(values) > 0 else 0.0,
                    'max': float(values.max()) if len(values) > 0 else 0.0,
                    'mean': float(values.mean()) if len(values) > 0 else 0.0,
                    'has_nan': df[col].isna().any(),
                    'is_normalized': True
                }
        
        return validation_results

