import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import json
import logging
from datetime import datetime

# Import our custom scoring components
from .preprocess import preprocess_data
from .normalize import DataNormalizer
from .weighting import ScoreWeightingEngine, WeightingStrategy, MetricType
from .outliers import OutlierDetector, OutlierMethod, OutlierAction
from .explain import ScoreExplainer, ExplanationType

logger = logging.getLogger(__name__)

class ScoringEngine:
    """
    Main scoring orchestrator that integrates all scoring components
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.normalizer = DataNormalizer()
        self.weighting_engine = ScoreWeightingEngine()
        self.outlier_detector = OutlierDetector()
        self.explainer = ScoreExplainer(openai_api_key)
        self.scoring_history = []
    
    def calculate_scores(self, df: pd.DataFrame, campaign_id: int,
                        config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate scores for the given dataset based on campaign criteria
        
        Args:
            df: Raw dataframe
            campaign_id: ID of the campaign to get scoring criteria
            config: Optional configuration for scoring process
            
        Returns:
            Dictionary containing scored dataframe and metadata
        """
        if config is None:
            config = {}
        
        start_time = datetime.now()
        
        try:
            # Step 1: Preprocess data
            logger.info("Starting data preprocessing...")
            processed_df = preprocess_data(df)
            
            # Step 2: Detect and handle outliers
            logger.info("Detecting outliers...")
            outlier_config = config.get('outlier_config', {
                'method': OutlierMethod.IQR,
                'action': OutlierAction.MARK
            })
            
            outlier_results = self.outlier_detector.detect_outliers(
                processed_df, 
                method=outlier_config['method']
            )
            
            processed_df = self.outlier_detector.handle_outliers(
                processed_df, 
                outlier_results, 
                action=outlier_config['action']
            )
            
            # Step 3: Normalize data
            logger.info("Normalizing data...")
            normalization_config = config.get('normalization_config', {
                'method': 'zscore',
                'columns': None
            })
            
            if normalization_config['method'] == 'zscore':
                processed_df = self.normalizer.z_score_normalize(
                    processed_df, 
                    columns=normalization_config['columns']
                )
            elif normalization_config['method'] == 'minmax':
                processed_df = self.normalizer.min_max_scale(
                    processed_df, 
                    columns=normalization_config['columns']
                )
            elif normalization_config['method'] == 'robust':
                processed_df = self.normalizer.robust_scale(
                    processed_df, 
                    columns=normalization_config['columns']
                )
            
            # Step 4: Configure weighting
            logger.info("Configuring weighting...")
            criteria = get_campaign_criteria(campaign_id)
            
            # Set campaign weights
            self.weighting_engine.set_campaign_weights(campaign_id, criteria['weights'])
            
            # Configure metrics
            for metric_name, metric_config in criteria.get('metric_configs', {}).items():
                self.weighting_engine.configure_metric(
                    metric_name,
                    MetricType(metric_config.get('type', 'continuous')),
                    metric_config.get('config', {})
                )
            
            # Step 5: Calculate weighted scores
            logger.info("Calculating weighted scores...")
            weighting_config = config.get('weighting_config', {
                'strategy': WeightingStrategy.LINEAR,
                'metrics': list(criteria['weights'].keys())
            })
            
            final_scores = self.weighting_engine.calculate_weighted_score(
                processed_df,
                campaign_id,
                weighting_config['metrics'],
                strategy=weighting_config['strategy']
            )
            
            # Step 6: Generate explanations
            logger.info("Generating explanations...")
            explanation_config = ExplanationConfig(
                explanation_type=ExplanationType.SCORE_BREAKDOWN,
                include_metrics=weighting_config['metrics']
            )
            
            explanation = self.explainer.generate_score_explanation(
                processed_df,
                final_scores,
                explanation_config,
                campaign_context=criteria
            )
            
            # Step 7: Prepare results
            result_df = processed_df.copy()
            result_df['final_score'] = final_scores
            result_df['score_rank'] = result_df['final_score'].rank(ascending=False)
            
            # Add outlier flags if outliers were marked
            if outlier_config['action'] == OutlierAction.MARK:
                for col, indices in outlier_results['outlier_indices'].items():
                    if indices:
                        outlier_flag_col = f"{col}_outlier"
                        result_df[outlier_flag_col] = False
                        result_df.loc[indices, outlier_flag_col] = True
            
            # Prepare comprehensive results
            results = {
                'scored_dataframe': result_df,
                'metadata': {
                    'campaign_id': campaign_id,
                    'total_records': len(result_df),
                    'processing_time': (datetime.now() - start_time).total_seconds(),
                    'average_score': final_scores.mean(),
                    'score_range': f"{final_scores.min():.2f} - {final_scores.max():.2f}",
                    'outlier_summary': outlier_results,
                    'normalization_summary': self.normalizer.get_scaling_summary(),
                    'weighting_summary': self.weighting_engine.get_weighting_summary(campaign_id)
                },
                'explanation': explanation,
                'outlier_report': self.outlier_detector.generate_outlier_report(
                    outlier_results, df
                ),
                'config_used': config
            }
            
            # Store in history
            self.scoring_history.append({
                'timestamp': datetime.now().isoformat(),
                'campaign_id': campaign_id,
                'results': results
            })
            
            logger.info(f"Scoring completed successfully for campaign {campaign_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error in scoring process: {e}")
            raise
    
    def get_scoring_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scoring history"""
        return self.scoring_history[-limit:]
    
    def compare_scoring_methods(self, df: pd.DataFrame, campaign_id: int,
                              methods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare different scoring configurations"""
        comparison_results = {}
        
        for i, method_config in enumerate(methods):
            try:
                results = self.calculate_scores(df, campaign_id, method_config)
                comparison_results[f"method_{i+1}"] = {
                    'config': method_config,
                    'average_score': results['metadata']['average_score'],
                    'score_range': results['metadata']['score_range'],
                    'processing_time': results['metadata']['processing_time']
                }
            except Exception as e:
                comparison_results[f"method_{i+1}"] = {'error': str(e)}
        
        return comparison_results

# Legacy function for backward compatibility
def calculate_scores(df: pd.DataFrame, campaign_id: int) -> pd.DataFrame:
    """
    Calculate scores for the given dataset based on campaign criteria
    
    Args:
        df: Preprocessed dataframe
        campaign_id: ID of the campaign to get scoring criteria
        
    Returns:
        DataFrame with calculated scores
    """
    engine = ScoringEngine()
    results = engine.calculate_scores(df, campaign_id)
    return results['scored_dataframe']

def get_campaign_criteria(campaign_id: int) -> Dict[str, Any]:
    """
    Get scoring criteria for a specific campaign
    This would typically query the database
    """
    # Placeholder criteria - in real implementation, this would come from database
    return {
        'criteria': {
            'financial_performance': {
                'columns': ['revenue', 'profit_margin', 'growth_rate'],
                'method': 'weighted_average'
            },
            'operational_efficiency': {
                'columns': ['productivity', 'efficiency_score'],
                'method': 'min_max_scaling'
            },
            'market_position': {
                'columns': ['market_share', 'brand_recognition'],
                'method': 'normalized_sum'
            }
        },
        'weights': {
            'financial_performance': 0.4,
            'operational_efficiency': 0.3,
            'market_position': 0.3
        }
    }

def calculate_component_scores(df: pd.DataFrame, criteria: Dict) -> Dict[str, pd.Series]:
    """Calculate scores for each component based on criteria"""
    component_scores = {}
    
    for component, config in criteria['criteria'].items():
        columns = config['columns']
        method = config['method']
        
        # Filter columns that exist in the dataframe
        available_columns = [col for col in columns if col in df.columns]
        
        if not available_columns:
            component_scores[component] = pd.Series(0, index=df.index)
            continue
        
        if method == 'weighted_average':
            component_scores[component] = df[available_columns].mean(axis=1)
        elif method == 'min_max_scaling':
            scaler = MinMaxScaler()
            scaled_values = scaler.fit_transform(df[available_columns])
            component_scores[component] = pd.Series(scaled_values.mean(axis=1), index=df.index)
        elif method == 'normalized_sum':
            normalized = (df[available_columns] - df[available_columns].mean()) / df[available_columns].std()
            component_scores[component] = normalized.sum(axis=1)
        else:
            # Default to simple average
            component_scores[component] = df[available_columns].mean(axis=1)
    
    return component_scores

def apply_weights(component_scores: Dict[str, pd.Series], weights: Dict[str, float]) -> pd.Series:
    """Apply weights to component scores to get final score"""
    final_score = pd.Series(0, index=next(iter(component_scores.values())).index)
    
    for component, score_series in component_scores.items():
        weight = weights.get(component, 0)
        final_score += weight * score_series
    
    # Normalize to 0-100 scale
    final_score = (final_score - final_score.min()) / (final_score.max() - final_score.min()) * 100
    
    return final_score

def generate_score_summary(scores_df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for the scores"""
    return {
        'total_records': len(scores_df),
        'average_score': scores_df['final_score'].mean(),
        'median_score': scores_df['final_score'].median(),
        'std_score': scores_df['final_score'].std(),
        'min_score': scores_df['final_score'].min(),
        'max_score': scores_df['final_score'].max(),
        'score_distribution': {
            'excellent': len(scores_df[scores_df['final_score'] >= 80]),
            'good': len(scores_df[(scores_df['final_score'] >= 60) & (scores_df['final_score'] < 80)]),
            'average': len(scores_df[(scores_df['final_score'] >= 40) & (scores_df['final_score'] < 60)]),
            'below_average': len(scores_df[(scores_df['final_score'] >= 20) & (scores_df['final_score'] < 40)]),
            'poor': len(scores_df[scores_df['final_score'] < 20])
        }
    } 