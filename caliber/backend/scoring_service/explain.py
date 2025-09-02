"""
Generate explanations for individual domain scores
"""

import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def generate_deterministic_explanation(
    domain: str, 
    score: float, 
    status: str, 
    metrics: Dict, 
    weights: Dict[str, float]
) -> str:
    """
    Generate a deterministic explanation for a domain's score
    
    Args:
        domain: Domain name
        score: Calculated score (0-100)
        status: Score status (Good/Moderate/Poor)
        metrics: Dictionary of metric values
        weights: Scoring weights used
        
    Returns:
        Explanation string
    """
    # Get primary driver based on weights
    primary_metric = max(weights.keys(), key=lambda k: weights[k])
    
    # Format metrics for readability
    cpm = metrics.get('cpm', 0)
    ctr = metrics.get('ctr', 0) * 100 if metrics.get('ctr') else 0  # Convert to percentage
    conv_rate = metrics.get('conversion_rate', 0) * 100 if metrics.get('conversion_rate') else 0
    
    # Build explanation based on score and primary metric
    if status == 'Good':
        if primary_metric == 'ctr':
            explanation = f"High CTR of {ctr:.2f}% drives strong performance"
        elif primary_metric == 'conversion_rate':
            explanation = f"Excellent conversion rate of {conv_rate:.2f}% leads to top score"
        else:  # cpm
            explanation = f"Efficient CPM of ${cpm:.2f} with solid engagement"
    
    elif status == 'Moderate':
        if primary_metric == 'ctr':
            explanation = f"Moderate CTR of {ctr:.2f}% with room for improvement"
        elif primary_metric == 'conversion_rate':
            explanation = f"Average conversion rate of {conv_rate:.2f}% shows potential"
        else:  # cpm
            explanation = f"CPM of ${cpm:.2f} is acceptable but could be optimized"
    
    else:  # Poor
        if primary_metric == 'ctr':
            explanation = f"Low CTR of {ctr:.2f}% significantly impacts performance"
        elif primary_metric == 'conversion_rate':
            explanation = f"Poor conversion rate of {conv_rate:.2f}% needs attention"
        else:  # cpm
            explanation = f"High CPM of ${cpm:.2f} reduces cost efficiency"
    
    return explanation


def generate_ai_explanation(
    domain: str, 
    score: float, 
    metrics: Dict, 
    weights: Dict[str, float]
) -> str:
    """
    Generate AI-powered explanation (placeholder for OpenAI integration)
    
    This is a placeholder that falls back to deterministic explanations.
    In a full implementation, this would call the OpenAI API.
    """
    # TODO: Implement OpenAI API call for more sophisticated explanations
    # For now, use deterministic explanation as fallback
    status = "Good" if score >= 70 else "Moderate" if score >= 40 else "Poor"
    return generate_deterministic_explanation(domain, score, status, metrics, weights)


def generate_explanations(df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
    """
    Generate explanations for all domains in the dataframe
    
    Args:
        df: DataFrame with scored domains
        weights: Scoring weights used
        
    Returns:
        DataFrame with explanations added
    """
    df = df.copy()
    
    explanations = []
    
    for _, row in df.iterrows():
        metrics = {
            'cpm': row.get('cpm', 0),
            'ctr': row.get('ctr', 0),
            'conversion_rate': row.get('conversion_rate', 0),
            'impressions': row.get('impressions', 0),
            'total_spend': row.get('total_spend', 0)
        }
        
        explanation = generate_deterministic_explanation(
            domain=row['domain'],
            score=row['score'],
            status=row['status'],
            metrics=metrics,
            weights=weights
        )
        
        explanations.append(explanation)
    
    df['explanation'] = explanations
    
    logger.info(f"Generated explanations for {len(df)} domains")
    
    return df


def get_performance_insights(df: pd.DataFrame, weights: Dict[str, float]) -> List[str]:
    """
    Generate high-level performance insights for the entire dataset
    
    Args:
        df: DataFrame with scored domains
        weights: Scoring weights used
        
    Returns:
        List of insight strings
    """
    insights = []
    
    # Overall performance distribution
    good_count = len(df[df['status'] == 'Good'])
    moderate_count = len(df[df['status'] == 'Moderate'])
    poor_count = len(df[df['status'] == 'Poor'])
    total_count = len(df)
    
    good_pct = (good_count / total_count * 100) if total_count > 0 else 0
    
    insights.append(f"{good_pct:.1f}% of domains achieve 'Good' performance scores")
    
    # Top performer insight
    if good_count > 0:
        top_domain = df.loc[df['score'].idxmax()]
        insights.append(f"Top performer: {top_domain['domain']} with score {top_domain['score']:.1f}")
    
    # Primary metric insight
    primary_metric = max(weights.keys(), key=lambda k: weights[k])
    if primary_metric == 'ctr':
        avg_ctr = df['ctr'].mean() * 100 if 'ctr' in df else 0
        insights.append(f"Average CTR across all domains: {avg_ctr:.2f}%")
    elif primary_metric == 'conversion_rate':
        avg_conv = df['conversion_rate'].mean() * 100 if 'conversion_rate' in df else 0
        insights.append(f"Average conversion rate: {avg_conv:.2f}%")
    
    # Cost efficiency insight
    if 'cpm' in df.columns:
        avg_cpm = df['cpm'].mean()
        efficient_domains = len(df[df['cpm'] < avg_cpm])
        insights.append(f"{efficient_domains} domains operate below average CPM of ${avg_cpm:.2f}")
    
    return insights