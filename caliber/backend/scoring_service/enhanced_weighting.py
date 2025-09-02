"""
Enhanced weighting system implementing document-specific scoring models
"""

from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class EnhancedWeighting:
    """Implements document-specific scoring models for different sources/channels/goals"""
    
    def __init__(self):
        # Document-specified scoring models
        self.scoring_models = {
            'PulsePoint': {
                'display': {
                    'Awareness': {
                        'ecpm': 0.35,  # lower is better
                        'ctr': 0.40,
                        'conversion_rate': 0.25
                    },
                    'Action': {
                        'ecpm': 0.15,  # lower is better
                        'ctr': 0.25,
                        'conversion_rate': 0.60
                    }
                },
                'video': {
                    'Awareness': {
                        'ecpm': 0.20,  # lower is better
                        'ctr': 0.10,
                        'completion_rate': 0.50,
                        'conversion_rate': 0.20
                    },
                    'Action': {
                        'ecpm': 0.20,  # lower is better
                        'ctr': 0.10,
                        'completion_rate': 0.50,
                        'conversion_rate': 0.20
                    }
                }
            },
            'TTD': {
                'display': {
                    'Awareness': {
                        'cpm': 0.15,  # lower is better
                        'ias_display_fully_in_view_1s': 0.25,
                        'ctr': 0.20,
                        'ad_load_rate': 0.20,  # lower is better
                        'ad_refresh_rate': 0.20  # lower is better
                    },
                    'Awareness_CTR_Sensitive': {
                        'cpm': 0.10,  # lower is better
                        'ias_display_fully_in_view_1s': 0.25,
                        'ctr': 0.30,
                        'ad_load_rate': 0.15,  # lower is better
                        'ad_refresh_rate': 0.20  # lower is better
                    },
                    'Action': {
                        'cpm': 0.10,  # lower is better
                        'ias_display_fully_in_view_1s': 0.10,
                        'conversion_rate': 0.30,
                        'ctr': 0.15,
                        'ad_load_rate': 0.15,  # lower is better
                        'ad_refresh_rate': 0.20  # lower is better
                    }
                },
                'video': {
                    'Awareness': {
                        'cpm': 0.10,  # lower is better
                        'sampled_in_view': 0.20,
                        'player_completion': 0.35,
                        'player_errors': 0.20,  # lower is better
                        'player_mute': 0.15  # lower is better
                    },
                    'Action': {
                        'cpm': 0.10,  # lower is better
                        'sampled_in_view': 0.20,
                        'player_completion': 0.35,
                        'player_errors': 0.20,  # lower is better
                        'player_mute': 0.15  # lower is better
                    }
                },
                'audio': {
                    'Awareness': {
                        'cpm': 0.10,  # lower is better
                        'sampled_in_view': 0.20,
                        'player_completion': 0.35,
                        'player_errors': 0.20,  # lower is better
                        'player_mute': 0.15  # lower is better
                    },
                    'Action': {
                        'cpm': 0.10,  # lower is better
                        'sampled_in_view': 0.20,
                        'player_completion': 0.35,
                        'player_errors': 0.20,  # lower is better
                        'player_mute': 0.15  # lower is better
                    }
                },
                'ctv': {
                    'Awareness': {
                        'tv_quality_index_ratio': 0.70,
                        'unique_id_ratio': 0.30
                    },
                    'Action': {
                        'tv_quality_index_ratio': 0.70,
                        'unique_id_ratio': 0.30
                    }
                }
            }
        }
    
    def get_scoring_model(self, source: str, channel: str, goal: str, ctr_sensitive: bool = False) -> Dict[str, float]:
        """
        Get scoring model weights based on source, channel, goal, and CTR sensitivity
        
        Args:
            source: Data source ('TTD' or 'PulsePoint')
            channel: Channel type
            goal: Campaign goal ('Awareness' or 'Action')
            ctr_sensitive: Whether CTR sensitivity applies (TTD Display Awareness only)
            
        Returns:
            Dictionary of metric weights
        """
        try:
            # Normalize channel name to lowercase
            channel_normalized = channel.lower()
            
            if source == 'TTD' and channel_normalized == 'display' and goal == 'Awareness' and ctr_sensitive:
                model_key = 'Awareness_CTR_Sensitive'
            else:
                model_key = goal
            
            weights = self.scoring_models[source][channel_normalized][model_key]
            logger.info(f"Retrieved scoring model for {source} {channel} {goal} (CTR sensitive: {ctr_sensitive}): {weights}")
            return weights.copy()
            
        except KeyError as e:
            logger.error(f"No scoring model found for {source} {channel} {goal}: {e}")
            # Return default weights
            return self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights as fallback"""
        return {
            'ctr': 0.40,
            'cpm': 0.30,
            'conversion_rate': 0.30
        }
    
    def get_metric_mapping(self, source: str, channel: str) -> Dict[str, str]:
        """
        Get mapping from weight keys to normalized feature columns
        
        Args:
            source: Data source
            channel: Channel type
            
        Returns:
            Dictionary mapping weight keys to feature column names
        """
        base_mapping = {
            # Common metrics
            'ctr': 'ctr_score_ready',
            'cpm': 'cpm_score_ready',
            'ecpm': 'ecpm_score_ready',
            'conversion_rate': 'conversion_rate_score_ready',
            
            # TTD specific
            'ias_display_fully_in_view_1s': 'ias_display_fully_in_view_1s_score_ready',
            'ad_load_rate': 'ad_load_rate_score_ready',
            'ad_refresh_rate': 'ad_refresh_rate_score_ready',
            'sampled_in_view': 'sampled_in_view_score_ready',
            'player_completion': 'player_completion_score_ready',
            'player_errors': 'player_errors_score_ready',
            'player_mute': 'player_mute_score_ready',
            'tv_quality_index_ratio': 'tv_quality_index_ratio_score_ready',
            'unique_id_ratio': 'unique_id_ratio_score_ready',
            
            # PulsePoint specific
            'completion_rate': 'completion_rate_score_ready'
        }
        
        return base_mapping
    
    def get_metric_direction(self, source: str, channel: str, goal: str) -> Dict[str, str]:
        """
        Get metric direction (higher-is-better vs lower-is-better)
        
        Args:
            source: Data source
            channel: Channel type
            goal: Campaign goal
            
        Returns:
            Dictionary mapping metrics to 'higher' or 'lower'
        """
        # Higher is better metrics
        higher_is_better = [
            'ctr', 'conversion_rate', 'completion_rate', 'ias_display_fully_in_view_1s',
            'sampled_in_view', 'player_completion', 'tv_quality_index_ratio', 'unique_id_ratio'
        ]
        
        # Lower is better metrics
        lower_is_better = [
            'cpm', 'ecpm', 'ad_load_rate', 'ad_refresh_rate', 'player_errors', 'player_mute'
        ]
        
        direction_map = {}
        
        # Set directions for all metrics
        for metric in higher_is_better:
            direction_map[metric] = 'higher'
        for metric in lower_is_better:
            direction_map[metric] = 'lower'
        
        return direction_map
    
    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """
        Validate that weights sum to 1.0
        
        Args:
            weights: Weight dictionary
            
        Returns:
            True if weights are valid
        """
        total_weight = sum(weights.values())
        is_valid = abs(total_weight - 1.0) < 0.001  # Small tolerance for floating point
        
        if not is_valid:
            logger.error(f"Weights don't sum to 1.0: {total_weight}")
        
        return is_valid
    
    def get_scoring_summary(self, source: str, channel: str, goal: str, ctr_sensitive: bool = False) -> Dict:
        """
        Get comprehensive scoring summary for the configuration
        
        Args:
            source: Data source
            channel: Channel type
            goal: Campaign goal
            ctr_sensitive: Whether CTR sensitivity applies
            
        Returns:
            Scoring configuration summary
        """
        weights = self.get_scoring_model(source, channel, goal, ctr_sensitive)
        metric_mapping = self.get_metric_mapping(source, channel)
        metric_direction = self.get_metric_direction(source, channel, goal)
        
        summary = {
            'source': source,
            'channel': channel,
            'goal': goal,
            'ctr_sensitive': ctr_sensitive,
            'weights': weights,
            'metric_mapping': metric_mapping,
            'metric_direction': metric_direction,
            'total_weight': sum(weights.values()),
            'metrics_count': len(weights),
            'validation': {
                'weights_valid': self.validate_weights(weights),
                'has_inverse_metrics': any(direction == 'lower' for direction in metric_direction.values())
            }
        }
        
        return summary
