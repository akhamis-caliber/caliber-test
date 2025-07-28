import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Enumeration of different metric types"""
    CONTINUOUS = "continuous"
    BINARY = "binary"
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    PERCENTAGE = "percentage"
    RATIO = "ratio"

class WeightingStrategy(Enum):
    """Enumeration of weighting strategies"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    CUSTOM = "custom"

class ScoreWeightingEngine:
    """
    Comprehensive weighting engine for scoring calculations
    """
    
    def __init__(self):
        self.weights = {}
        self.metric_configs = {}
        self.weighting_history = []
    
    def set_campaign_weights(self, campaign_id: int, weights: Dict[str, float]) -> None:
        """
        Set weights for a specific campaign
        
        Args:
            campaign_id: Campaign identifier
            weights: Dictionary of metric names to weights
        """
        # Validate weights sum to 1.0
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            logger.warning(f"Weights for campaign {campaign_id} don't sum to 1.0: {total_weight}")
            # Normalize weights
            weights = {k: v / total_weight for k, v in weights.items()}
        
        self.weights[campaign_id] = weights
        logger.info(f"Set weights for campaign {campaign_id}: {weights}")
    
    def configure_metric(self, metric_name: str, metric_type: MetricType, 
                        config: Dict[str, Any]) -> None:
        """
        Configure a metric with its type and parameters
        
        Args:
            metric_name: Name of the metric
            metric_type: Type of the metric
            config: Configuration dictionary
        """
        self.metric_configs[metric_name] = {
            'type': metric_type,
            'config': config
        }
    
    def calculate_weighted_score(self, df: pd.DataFrame, campaign_id: int,
                               metrics: List[str], strategy: WeightingStrategy = WeightingStrategy.LINEAR,
                               custom_function: Optional[callable] = None) -> pd.Series:
        """
        Calculate weighted scores for a dataset
        
        Args:
            df: Input dataframe
            campaign_id: Campaign identifier
            metrics: List of metric columns to include
            strategy: Weighting strategy to use
            custom_function: Custom weighting function (for CUSTOM strategy)
            
        Returns:
            Weighted score series
        """
        if campaign_id not in self.weights:
            raise ValueError(f"No weights configured for campaign {campaign_id}")
        
        campaign_weights = self.weights[campaign_id]
        
        # Filter metrics that exist in both dataframe and weights
        available_metrics = [m for m in metrics if m in df.columns and m in campaign_weights]
        
        if not available_metrics:
            raise ValueError("No valid metrics found for scoring")
        
        # Calculate individual metric scores
        metric_scores = {}
        for metric in available_metrics:
            metric_scores[metric] = self._calculate_metric_score(df, metric)
        
        # Apply weighting strategy
        if strategy == WeightingStrategy.LINEAR:
            final_score = self._apply_linear_weights(metric_scores, campaign_weights)
        elif strategy == WeightingStrategy.EXPONENTIAL:
            final_score = self._apply_exponential_weights(metric_scores, campaign_weights)
        elif strategy == WeightingStrategy.LOGARITHMIC:
            final_score = self._apply_logarithmic_weights(metric_scores, campaign_weights)
        elif strategy == WeightingStrategy.CUSTOM:
            if custom_function is None:
                raise ValueError("Custom function required for CUSTOM strategy")
            final_score = custom_function(metric_scores, campaign_weights)
        else:
            raise ValueError(f"Unknown weighting strategy: {strategy}")
        
        # Store weighting history
        self.weighting_history.append({
            'campaign_id': campaign_id,
            'strategy': strategy,
            'metrics_used': available_metrics,
            'weights_applied': {m: campaign_weights[m] for m in available_metrics}
        })
        
        return final_score
    
    def _calculate_metric_score(self, df: pd.DataFrame, metric: str) -> pd.Series:
        """
        Calculate score for a single metric based on its type and configuration
        
        Args:
            df: Input dataframe
            metric: Metric column name
            
        Returns:
            Score series for the metric
        """
        if metric not in self.metric_configs:
            # Default to continuous metric
            return self._normalize_continuous_metric(df[metric])
        
        config = self.metric_configs[metric]
        metric_type = config['type']
        params = config['config']
        
        if metric_type == MetricType.CONTINUOUS:
            return self._normalize_continuous_metric(df[metric], params)
        elif metric_type == MetricType.BINARY:
            return self._normalize_binary_metric(df[metric], params)
        elif metric_type == MetricType.CATEGORICAL:
            return self._normalize_categorical_metric(df[metric], params)
        elif metric_type == MetricType.ORDINAL:
            return self._normalize_ordinal_metric(df[metric], params)
        elif metric_type == MetricType.PERCENTAGE:
            return self._normalize_percentage_metric(df[metric], params)
        elif metric_type == MetricType.RATIO:
            return self._normalize_ratio_metric(df[metric], params)
        else:
            logger.warning(f"Unknown metric type: {metric_type}")
            return self._normalize_continuous_metric(df[metric])
    
    def _normalize_continuous_metric(self, series: pd.Series, params: Optional[Dict] = None) -> pd.Series:
        """Normalize continuous metric to 0-1 scale"""
        if params is None:
            params = {}
        
        method = params.get('method', 'minmax')
        
        if method == 'minmax':
            min_val = series.min()
            max_val = series.max()
            if max_val > min_val:
                return (series - min_val) / (max_val - min_val)
            else:
                return pd.Series(0.5, index=series.index)
        elif method == 'zscore':
            mean_val = series.mean()
            std_val = series.std()
            if std_val > 0:
                z_scores = (series - mean_val) / std_val
                # Convert to 0-1 scale using sigmoid
                return 1 / (1 + np.exp(-z_scores))
            else:
                return pd.Series(0.5, index=series.index)
        elif method == 'percentile':
            return series.rank(pct=True)
        else:
            return self._normalize_continuous_metric(series, {'method': 'minmax'})
    
    def _normalize_binary_metric(self, series: pd.Series, params: Dict) -> pd.Series:
        """Normalize binary metric"""
        true_value = params.get('true_value', 1)
        false_value = params.get('false_value', 0)
        
        return (series == true_value).astype(float)
    
    def _normalize_categorical_metric(self, series: pd.Series, params: Dict) -> pd.Series:
        """Normalize categorical metric using mapping"""
        value_mapping = params.get('value_mapping', {})
        
        if not value_mapping:
            # Default to one-hot encoding
            return pd.get_dummies(series).iloc[:, 0] if len(pd.get_dummies(series).columns) > 0 else pd.Series(0, index=series.index)
        
        return series.map(value_mapping).fillna(0)
    
    def _normalize_ordinal_metric(self, series: pd.Series, params: Dict) -> pd.Series:
        """Normalize ordinal metric"""
        order_mapping = params.get('order_mapping', {})
        
        if not order_mapping:
            # Default to rank-based normalization
            return series.rank(pct=True)
        
        # Map to numerical values and normalize
        numerical_series = series.map(order_mapping)
        return self._normalize_continuous_metric(numerical_series)
    
    def _normalize_percentage_metric(self, series: pd.Series, params: Dict) -> pd.Series:
        """Normalize percentage metric"""
        # Assume percentage is already in 0-100 scale
        return series / 100.0
    
    def _normalize_ratio_metric(self, series: pd.Series, params: Dict) -> pd.Series:
        """Normalize ratio metric"""
        target_ratio = params.get('target_ratio', 1.0)
        tolerance = params.get('tolerance', 0.1)
        
        # Calculate distance from target ratio
        distance = np.abs(series - target_ratio)
        
        # Convert to score (closer to target = higher score)
        max_distance = tolerance * 2
        score = np.maximum(0, 1 - (distance / max_distance))
        
        return pd.Series(score, index=series.index)
    
    def _apply_linear_weights(self, metric_scores: Dict[str, pd.Series], 
                            weights: Dict[str, float]) -> pd.Series:
        """Apply linear weighting"""
        final_score = pd.Series(0, index=next(iter(metric_scores.values())).index)
        
        for metric, score in metric_scores.items():
            if metric in weights:
                final_score += weights[metric] * score
        
        return final_score
    
    def _apply_exponential_weights(self, metric_scores: Dict[str, pd.Series], 
                                 weights: Dict[str, float], exponent: float = 2.0) -> pd.Series:
        """Apply exponential weighting"""
        final_score = pd.Series(0, index=next(iter(metric_scores.values())).index)
        
        for metric, score in metric_scores.items():
            if metric in weights:
                # Apply exponential transformation to emphasize differences
                weighted_score = weights[metric] * (score ** exponent)
                final_score += weighted_score
        
        # Normalize to 0-1 scale
        if final_score.max() > 0:
            final_score = final_score / final_score.max()
        
        return final_score
    
    def _apply_logarithmic_weights(self, metric_scores: Dict[str, pd.Series], 
                                 weights: Dict[str, float]) -> pd.Series:
        """Apply logarithmic weighting"""
        final_score = pd.Series(0, index=next(iter(metric_scores.values())).index)
        
        for metric, score in metric_scores.items():
            if metric in weights:
                # Apply logarithmic transformation to reduce impact of extreme values
                log_score = np.log(score + 1e-8)  # Add small constant to avoid log(0)
                weighted_score = weights[metric] * log_score
                final_score += weighted_score
        
        # Normalize to 0-1 scale
        if final_score.max() > final_score.min():
            final_score = (final_score - final_score.min()) / (final_score.max() - final_score.min())
        
        return final_score
    
    def calculate_composite_score(self, df: pd.DataFrame, campaign_id: int,
                                composite_config: Dict[str, Any]) -> pd.Series:
        """
        Calculate composite score using multiple sub-scores
        
        Args:
            df: Input dataframe
            campaign_id: Campaign identifier
            composite_config: Configuration for composite scoring
            
        Returns:
            Composite score series
        """
        sub_scores = {}
        
        for sub_score_name, sub_config in composite_config['sub_scores'].items():
            metrics = sub_config['metrics']
            weight = sub_config['weight']
            
            # Calculate sub-score
            sub_score = self.calculate_weighted_score(df, campaign_id, metrics)
            sub_scores[sub_score_name] = sub_score * weight
        
        # Combine sub-scores
        composite_score = pd.Series(0, index=df.index)
        for sub_score in sub_scores.values():
            composite_score += sub_score
        
        return composite_score
    
    def apply_dynamic_weights(self, df: pd.DataFrame, campaign_id: int,
                            base_weights: Dict[str, float],
                            dynamic_factors: Dict[str, str]) -> Dict[str, float]:
        """
        Apply dynamic weights based on data characteristics
        
        Args:
            df: Input dataframe
            campaign_id: Campaign identifier
            base_weights: Base weights
            dynamic_factors: Dictionary mapping metrics to dynamic factors
            
        Returns:
            Adjusted weights
        """
        adjusted_weights = base_weights.copy()
        
        for metric, factor in dynamic_factors.items():
            if metric in df.columns and metric in base_weights:
                if factor == 'variance':
                    # Adjust weight based on variance
                    variance = df[metric].var()
                    if variance > 0:
                        adjustment = 1 / (1 + variance)
                        adjusted_weights[metric] *= adjustment
                elif factor == 'correlation':
                    # Adjust weight based on correlation with other metrics
                    correlations = df[metric].corr(df[base_weights.keys()])
                    avg_correlation = correlations.mean()
                    adjustment = 1 + avg_correlation
                    adjusted_weights[metric] *= adjustment
        
        # Renormalize weights
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}
        
        return adjusted_weights
    
    def get_weighting_summary(self, campaign_id: int) -> Dict[str, Any]:
        """Get summary of weighting configuration for a campaign"""
        if campaign_id not in self.weights:
            return {}
        
        return {
            'campaign_id': campaign_id,
            'weights': self.weights[campaign_id],
            'metric_configs': self.metric_configs,
            'recent_history': self.weighting_history[-5:] if self.weighting_history else []
        }
    
    def validate_weights(self, campaign_id: int) -> Dict[str, Any]:
        """Validate weighting configuration"""
        if campaign_id not in self.weights:
            return {'valid': False, 'error': 'Campaign not found'}
        
        weights = self.weights[campaign_id]
        total_weight = sum(weights.values())
        
        validation_result = {
            'valid': True,
            'total_weight': total_weight,
            'warnings': []
        }
        
        if abs(total_weight - 1.0) > 1e-6:
            validation_result['warnings'].append(f"Weights don't sum to 1.0: {total_weight}")
        
        negative_weights = [k for k, v in weights.items() if v < 0]
        if negative_weights:
            validation_result['warnings'].append(f"Negative weights found: {negative_weights}")
        
        return validation_result 