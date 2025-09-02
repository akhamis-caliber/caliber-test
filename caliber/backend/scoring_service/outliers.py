"""
Outlier detection and handling for scoring pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> Tuple[pd.Series, Dict]:
    """
    Detect outliers using Interquartile Range (IQR) method
    
    Args:
        series: Input data series
        multiplier: IQR multiplier (1.5 is standard, 3.0 is more conservative)
        
    Returns:
        Tuple of (outlier_mask, detection_summary)
    """
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    outliers = (series < lower_bound) | (series > upper_bound)
    
    summary = {
        'method': 'iqr',
        'q1': float(q1),
        'q3': float(q3),
        'iqr': float(iqr),
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'outlier_count': int(outliers.sum()),
        'outlier_percentage': float(outliers.sum() / len(series) * 100)
    }
    
    return outliers, summary


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> Tuple[pd.Series, Dict]:
    """
    Detect outliers using Z-score method
    
    Args:
        series: Input data series
        threshold: Z-score threshold (typically 2.5 or 3.0)
        
    Returns:
        Tuple of (outlier_mask, detection_summary)
    """
    z_scores = np.abs(stats.zscore(series))
    outliers = z_scores > threshold
    
    summary = {
        'method': 'zscore',
        'threshold': threshold,
        'max_zscore': float(z_scores.max()),
        'mean_zscore': float(z_scores.mean()),
        'outlier_count': int(outliers.sum()),
        'outlier_percentage': float(outliers.sum() / len(series) * 100)
    }
    
    return outliers, summary


def detect_outliers_modified_zscore(series: pd.Series, threshold: float = 3.5) -> Tuple[pd.Series, Dict]:
    """
    Detect outliers using Modified Z-score (more robust to extreme outliers)
    
    Args:
        series: Input data series
        threshold: Modified Z-score threshold
        
    Returns:
        Tuple of (outlier_mask, detection_summary)
    """
    median = np.median(series)
    mad = np.median(np.abs(series - median))  # Median Absolute Deviation
    
    # Avoid division by zero
    if mad == 0:
        mad = 1.4826 * np.median(np.abs(series - np.mean(series)))
    
    modified_z_scores = 0.6745 * (series - median) / mad
    outliers = np.abs(modified_z_scores) > threshold
    
    summary = {
        'method': 'modified_zscore',
        'threshold': threshold,
        'median': float(median),
        'mad': float(mad),
        'max_modified_zscore': float(np.abs(modified_z_scores).max()),
        'outlier_count': int(outliers.sum()),
        'outlier_percentage': float(outliers.sum() / len(series) * 100)
    }
    
    return outliers, summary


def winsorize_outliers(series: pd.Series, percentiles: Tuple[float, float] = (0.01, 0.99)) -> Tuple[pd.Series, Dict]:
    """
    Winsorize outliers by capping at specified percentiles
    
    Args:
        series: Input data series
        percentiles: Lower and upper percentiles for winsorization
        
    Returns:
        Tuple of (winsorized_series, winsorization_summary)
    """
    lower_percentile, upper_percentile = percentiles
    
    lower_bound = series.quantile(lower_percentile)
    upper_bound = series.quantile(upper_percentile)
    
    # Count values that will be changed
    lower_outliers = (series < lower_bound).sum()
    upper_outliers = (series > upper_bound).sum()
    
    # Apply winsorization
    winsorized = series.copy()
    winsorized = winsorized.clip(lower=lower_bound, upper=upper_bound)
    
    summary = {
        'method': 'winsorization',
        'percentiles': percentiles,
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'lower_outliers_capped': int(lower_outliers),
        'upper_outliers_capped': int(upper_outliers),
        'total_values_changed': int(lower_outliers + upper_outliers),
        'percentage_changed': float((lower_outliers + upper_outliers) / len(series) * 100)
    }
    
    return winsorized, summary


def remove_extreme_outliers(df: pd.DataFrame, method: str = 'iqr') -> Tuple[pd.DataFrame, Dict]:
    """
    Remove extreme outliers that would distort scoring
    
    Args:
        df: Input DataFrame
        method: Outlier detection method ('iqr', 'zscore', 'modified_zscore')
        
    Returns:
        Tuple of (cleaned_dataframe, removal_summary)
    """
    df = df.copy()
    initial_rows = len(df)
    
    # Metrics to check for outliers
    metrics_to_check = ['cpm', 'ctr', 'conversion_rate', 'impressions', 'total_spend']
    
    removal_summary = {
        'method': method,
        'initial_rows': initial_rows,
        'metrics_checked': [],
        'outlier_details': {}
    }
    
    # Track which rows to remove
    rows_to_remove = pd.Series(False, index=df.index)
    
    for metric in metrics_to_check:
        if metric not in df.columns or df[metric].isna().all():
            continue
            
        valid_data = df[metric].dropna()
        if len(valid_data) < 10:  # Need minimum data for outlier detection
            continue
            
        removal_summary['metrics_checked'].append(metric)
        
        # Detect outliers
        if method == 'iqr':
            outliers, details = detect_outliers_iqr(valid_data, multiplier=3.0)  # Conservative
        elif method == 'zscore':
            outliers, details = detect_outliers_zscore(valid_data, threshold=4.0)  # Very conservative
        elif method == 'modified_zscore':
            outliers, details = detect_outliers_modified_zscore(valid_data, threshold=4.5)
        else:
            logger.warning(f"Unknown outlier detection method: {method}")
            continue
        
        removal_summary['outlier_details'][metric] = details
        
        # Mark rows for removal (only extreme outliers)
        if details['outlier_percentage'] < 20:  # Don't remove if too many outliers
            rows_to_remove[valid_data[outliers].index] = True
    
    # Remove outlier rows
    df_clean = df[~rows_to_remove]
    
    removal_summary.update({
        'final_rows': len(df_clean),
        'rows_removed': initial_rows - len(df_clean),
        'removal_percentage': float((initial_rows - len(df_clean)) / initial_rows * 100)
    })
    
    logger.info(f"Removed {removal_summary['rows_removed']} outlier rows ({removal_summary['removal_percentage']:.2f}%)")
    
    return df_clean, removal_summary


def winsorize_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Apply winsorization to key metrics to reduce impact of outliers
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (dataframe_with_winsorized_columns, winsorization_summary)
    """
    df = df.copy()
    
    # Metrics to winsorize and their percentiles
    winsorization_config = {
        'cpm': (0.01, 0.99),  # Cap extreme CPM values
        'ctr': (0.005, 0.995),  # Cap extreme CTR values  
        'conversion_rate': (0.005, 0.995),  # Cap extreme conversion rates
        'total_spend': (0.02, 0.98),  # Less aggressive for spend
        'impressions': (0.02, 0.98)   # Less aggressive for impressions
    }
    
    winsorization_summary = {
        'metrics_winsorized': [],
        'details': {}
    }
    
    for metric, percentiles in winsorization_config.items():
        if metric not in df.columns or df[metric].isna().all():
            continue
            
        valid_data = df[metric].dropna()
        if len(valid_data) < 10:  # Need minimum data
            continue
            
        # Apply winsorization
        winsorized, details = winsorize_outliers(valid_data, percentiles)
        
        # Create winsorized column
        winsorized_col = f'{metric}_winsorized'
        df[winsorized_col] = df[metric].copy()
        df.loc[valid_data.index, winsorized_col] = winsorized
        
        winsorization_summary['metrics_winsorized'].append(metric)
        winsorization_summary['details'][metric] = details
        
        logger.info(f"Winsorized '{metric}': {details['total_values_changed']} values changed")
    
    return df, winsorization_summary


def handle_outliers_for_scoring(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Complete outlier handling pipeline for scoring
    
    Args:
        df: Input DataFrame with campaign data
        
    Returns:
        Tuple of (processed_dataframe, outlier_handling_summary)
    """
    logger.info(f"Starting outlier handling for {len(df)} rows")
    
    # Step 1: Remove extreme outliers that would distort results
    df_no_extremes, removal_summary = remove_extreme_outliers(df, method='modified_zscore')
    
    # Step 2: Winsorize remaining outliers
    df_winsorized, winsorization_summary = winsorize_metrics(df_no_extremes)
    
    # Combine summaries
    complete_summary = {
        'initial_rows': len(df),
        'final_rows': len(df_winsorized),
        'extreme_outlier_removal': removal_summary,
        'winsorization': winsorization_summary,
        'total_processing_effect': {
            'rows_removed': removal_summary['rows_removed'],
            'metrics_winsorized': len(winsorization_summary['metrics_winsorized'])
        }
    }
    
    logger.info(f"Outlier handling completed: {len(df_winsorized)} rows remaining")
    return df_winsorized, complete_summary