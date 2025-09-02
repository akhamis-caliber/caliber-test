"""
Weighting strategies for different campaign goals and sensitivities
"""

from typing import Dict, Tuple
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def get_base_weights(goal: str) -> Dict[str, float]:
    """
    Get base weights for different campaign goals
    
    Args:
        goal: Campaign goal ('Awareness' or 'Action')
        
    Returns:
        Dictionary of metric weights
    """
    if goal.lower() == 'awareness':
        return settings.SCORE_WEIGHTS_AWARENESS.copy()
    elif goal.lower() == 'action':
        return settings.SCORE_WEIGHTS_ACTION.copy()
    else:
        # Default to awareness weights
        logger.warning(f"Unknown goal '{goal}', using awareness weights")
        return settings.SCORE_WEIGHTS_AWARENESS.copy()


def apply_ctr_sensitivity(weights: Dict[str, float], ctr_sensitive: bool) -> Dict[str, float]:
    """
    Adjust weights based on CTR sensitivity
    
    Args:
        weights: Base weights dictionary
        ctr_sensitive: Whether to boost CTR importance
        
    Returns:
        Adjusted weights dictionary
    """
    if not ctr_sensitive:
        return weights
    
    adjusted_weights = weights.copy()
    boost = settings.CTR_SENSITIVITY_BOOST
    
    # Boost CTR weight
    adjusted_weights['ctr'] += boost
    
    # Reduce other weights proportionally to maintain total = 1.0
    other_metrics = [k for k in adjusted_weights.keys() if k != 'ctr']
    total_other_weight = sum(adjusted_weights[k] for k in other_metrics)
    
    if total_other_weight > 0:
        # Calculate reduction factor
        available_weight = 1.0 - adjusted_weights['ctr']
        reduction_factor = available_weight / total_other_weight
        
        # Apply reduction
        for metric in other_metrics:
            adjusted_weights[metric] *= reduction_factor
    
    # Ensure weights sum to 1.0 (handle floating point precision)
    total_weight = sum(adjusted_weights.values())
    if abs(total_weight - 1.0) > 0.001:  # Small tolerance for floating point errors
        # Normalize weights
        for metric in adjusted_weights:
            adjusted_weights[metric] /= total_weight
    
    logger.info(f"Applied CTR sensitivity boost: {adjusted_weights}")
    return adjusted_weights


def calculate_weights(goal: str, ctr_sensitive: bool = False) -> Tuple[Dict[str, float], Dict]:
    """
    Calculate final weights for scoring based on campaign configuration
    
    Args:
        goal: Campaign goal ('Awareness' or 'Action')
        ctr_sensitive: Whether to boost CTR importance
        
    Returns:
        Tuple of (final_weights, weight_calculation_summary)
    """
    # Get base weights
    base_weights = get_base_weights(goal)
    
    # Apply CTR sensitivity
    final_weights = apply_ctr_sensitivity(base_weights, ctr_sensitive)
    
    # Create summary
    summary = {
        'goal': goal,
        'ctr_sensitive': ctr_sensitive,
        'base_weights': base_weights,
        'final_weights': final_weights,
        'ctr_boost_applied': ctr_sensitive,
        'total_weight': sum(final_weights.values())
    }
    
    # Validate weights
    total = sum(final_weights.values())
    if abs(total - 1.0) > 0.01:  # Allow small tolerance
        logger.error(f"Weights don't sum to 1.0: {total}")
        raise ValueError(f"Invalid weights sum: {total}")
    
    logger.info(f"Calculated weights for {goal} goal (CTR sensitive: {ctr_sensitive}): {final_weights}")
    return final_weights, summary


def get_metric_mapping() -> Dict[str, str]:
    """
    Get mapping from weight keys to normalized feature columns
    
    Returns:
        Dictionary mapping weight keys to feature column names
    """
    return {
        'ctr': 'ctr_score_ready',
        'cpm': 'cpm_score_ready',
        'conversion_rate': 'conversion_rate_score_ready'
    }


def validate_weights_and_features(weights: Dict[str, float], available_features: list) -> bool:
    """
    Validate that all required features are available for the given weights
    
    Args:
        weights: Weight dictionary
        available_features: List of available feature columns
        
    Returns:
        True if all required features are available
    """
    metric_mapping = get_metric_mapping()
    
    missing_features = []
    for metric in weights.keys():
        if metric in metric_mapping:
            required_feature = metric_mapping[metric]
            if required_feature not in available_features:
                missing_features.append(required_feature)
        else:
            logger.warning(f"No feature mapping found for metric '{metric}'")
    
    if missing_features:
        logger.error(f"Missing required features for scoring: {missing_features}")
        return False
    
    return True


def apply_custom_weights(base_weights: Dict[str, float], custom_adjustments: Dict[str, float]) -> Dict[str, float]:
    """
    Apply custom weight adjustments (for future extensibility)
    
    Args:
        base_weights: Base weight configuration
        custom_adjustments: Custom adjustments to apply
        
    Returns:
        Adjusted weights
    """
    adjusted_weights = base_weights.copy()
    
    for metric, adjustment in custom_adjustments.items():
        if metric in adjusted_weights:
            adjusted_weights[metric] += adjustment
    
    # Ensure non-negative weights
    for metric in adjusted_weights:
        adjusted_weights[metric] = max(0, adjusted_weights[metric])
    
    # Normalize to sum to 1.0
    total = sum(adjusted_weights.values())
    if total > 0:
        for metric in adjusted_weights:
            adjusted_weights[metric] /= total
    
    logger.info(f"Applied custom weight adjustments: {adjusted_weights}")
    return adjusted_weights