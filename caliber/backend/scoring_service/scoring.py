"""
Core scoring algorithm that combines normalized metrics with weights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def calculate_weighted_score(
    df: pd.DataFrame, 
    weights: Dict[str, float], 
    feature_columns: List[str]
) -> Tuple[pd.Series, Dict]:
    """
    Calculate weighted composite scores from normalized features
    
    Args:
        df: DataFrame with normalized features
        weights: Weight dictionary for each metric
        feature_columns: List of normalized feature columns
        
    Returns:
        Tuple of (scores_series, scoring_summary)
    """
    from scoring_service.weighting import get_metric_mapping
    
    metric_mapping = get_metric_mapping()
    
    # Initialize scores
    scores = pd.Series(0.0, index=df.index)
    
    # Track which weights were actually used
    weights_used = {}
    missing_features = []
    
    for metric, weight in weights.items():
        if metric in metric_mapping:
            feature_col = metric_mapping[metric]
            
            if feature_col in feature_columns and feature_col in df.columns:
                # Add weighted contribution
                feature_values = df[feature_col].fillna(0)  # Fill NaN with 0
                scores += weight * feature_values
                weights_used[metric] = weight
                
                logger.debug(f"Added {metric} with weight {weight}")
            else:
                missing_features.append(feature_col)
                logger.warning(f"Feature '{feature_col}' not available for metric '{metric}'")
    
    # Handle case where some features are missing
    if missing_features:
        logger.warning(f"Missing features: {missing_features}")
        # Renormalize weights for available features
        total_used_weight = sum(weights_used.values())
        if total_used_weight > 0:
            for metric in weights_used:
                weights_used[metric] = weights_used[metric] / total_used_weight
            
            # Recalculate scores with renormalized weights
            scores = pd.Series(0.0, index=df.index)
            for metric, weight in weights_used.items():
                feature_col = metric_mapping[metric]
                feature_values = df[feature_col].fillna(0)
                scores += weight * feature_values
    
    summary = {
        'weights_requested': weights,
        'weights_used': weights_used,
        'missing_features': missing_features,
        'total_weight_used': sum(weights_used.values()),
        'score_stats': {
            'min': float(scores.min()),
            'max': float(scores.max()),
            'mean': float(scores.mean()),
            'median': float(scores.median()),
            'std': float(scores.std())
        }
    }
    
    return scores, summary


def scale_to_100(scores: pd.Series) -> Tuple[pd.Series, Dict]:
    """
    Scale scores to 0-100 range
    
    Args:
        scores: Raw weighted scores
        
    Returns:
        Tuple of (scaled_scores, scaling_summary)
    """
    min_score = scores.min()
    max_score = scores.max()
    
    # Handle edge case where all scores are the same
    if min_score == max_score:
        logger.warning(f"All scores are identical ({min_score}), setting all to 50")
        scaled = pd.Series(50.0, index=scores.index)
        summary = {
            'method': 'uniform',
            'original_min': float(min_score),
            'original_max': float(max_score),
            'scaled_min': 50.0,
            'scaled_max': 50.0
        }
        return scaled, summary
    
    # Scale to 0-100
    scaled = ((scores - min_score) / (max_score - min_score)) * 100
    
    summary = {
        'method': 'min_max_100',
        'original_min': float(min_score),
        'original_max': float(max_score),
        'scaled_min': float(scaled.min()),
        'scaled_max': float(scaled.max()),
        'scaled_mean': float(scaled.mean()),
        'scaled_median': float(scaled.median())
    }
    
    return scaled, summary


def assign_status_categories(scores: pd.Series) -> Tuple[pd.Series, Dict]:
    """
    Assign status categories based on score thresholds
    
    Args:
        scores: Scores in 0-100 range
        
    Returns:
        Tuple of (status_series, categorization_summary)
    """
    good_threshold = settings.SCORE_THRESHOLD_GOOD
    moderate_threshold = settings.SCORE_THRESHOLD_MODERATE
    
    # Assign status categories
    status = pd.Series('Poor', index=scores.index)
    status[scores >= moderate_threshold] = 'Moderate'
    status[scores >= good_threshold] = 'Good'
    
    # Calculate distribution
    status_counts = status.value_counts()
    
    summary = {
        'thresholds': {
            'good': good_threshold,
            'moderate': moderate_threshold
        },
        'distribution': {
            'Good': int(status_counts.get('Good', 0)),
            'Moderate': int(status_counts.get('Moderate', 0)),
            'Poor': int(status_counts.get('Poor', 0))
        },
        'percentages': {
            'Good': float(status_counts.get('Good', 0) / len(status) * 100),
            'Moderate': float(status_counts.get('Moderate', 0) / len(status) * 100),
            'Poor': float(status_counts.get('Poor', 0) / len(status) * 100)
        }
    }
    
    return status, summary


def calculate_domain_scores(
    df: pd.DataFrame, 
    weights: Dict[str, float], 
    feature_columns: List[str]
) -> Tuple[pd.DataFrame, Dict]:
    """
    Calculate complete scoring for domains/publishers
    
    Args:
        df: DataFrame with normalized features
        weights: Weight dictionary
        feature_columns: List of normalized feature columns
        
    Returns:
        Tuple of (dataframe_with_scores, complete_scoring_summary)
    """
    df = df.copy()
    
    logger.info(f"Calculating scores for {len(df)} rows")
    
    # Step 1: Calculate weighted scores
    raw_scores, scoring_summary = calculate_weighted_score(df, weights, feature_columns)
    
    # Step 2: Scale to 0-100
    scaled_scores, scaling_summary = scale_to_100(raw_scores)
    
    # Step 3: Assign status categories
    status, status_summary = assign_status_categories(scaled_scores)
    
    # Add results to dataframe
    df['score'] = scaled_scores
    df['status'] = status
    df['raw_score'] = raw_scores
    
    # Combine all summaries
    complete_summary = {
        'rows_scored': len(df),
        'scoring_details': scoring_summary,
        'scaling_details': scaling_summary,
        'status_details': status_summary,
        'final_score_distribution': {
            'min': float(scaled_scores.min()),
            'max': float(scaled_scores.max()),
            'mean': float(scaled_scores.mean()),
            'median': float(scaled_scores.median()),
            'q25': float(scaled_scores.quantile(0.25)),
            'q75': float(scaled_scores.quantile(0.75))
        }
    }
    
    logger.info(f"Scoring completed: {complete_summary['status_details']['distribution']}")
    
    return df, complete_summary


def rank_domains(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Add ranking information to scored domains
    
    Args:
        df: DataFrame with scores
        
    Returns:
        Tuple of (dataframe_with_ranks, ranking_summary)
    """
    df = df.copy()
    
    # Add overall rank (1 is best)
    df['rank'] = df['score'].rank(method='dense', ascending=False).astype(int)
    
    # Add percentile rank
    df['percentile'] = df['score'].rank(pct=True) * 100
    
    # Identify top/bottom performers
    total_rows = len(df)
    top_25_count = max(1, int(total_rows * 0.25))
    bottom_25_count = max(1, int(total_rows * 0.25))
    
    df['performance_tier'] = 'Middle'
    df.loc[df['rank'] <= top_25_count, 'performance_tier'] = 'Top'
    df.loc[df['rank'] > (total_rows - bottom_25_count), 'performance_tier'] = 'Bottom'
    
    # Create ranking summary
    tier_counts = df['performance_tier'].value_counts()
    
    summary = {
        'total_domains': total_rows,
        'ranking_method': 'dense (no gaps for ties)',
        'percentile_method': 'standard',
        'performance_tiers': {
            'Top': int(tier_counts.get('Top', 0)),
            'Middle': int(tier_counts.get('Middle', 0)),
            'Bottom': int(tier_counts.get('Bottom', 0))
        },
        'top_performers': df.nlargest(5, 'score')[['score', 'status']].to_dict('records'),
        'bottom_performers': df.nsmallest(5, 'score')[['score', 'status']].to_dict('records')
    }
    
    logger.info(f"Ranking completed: {summary['performance_tiers']}")
    
    return df, summary