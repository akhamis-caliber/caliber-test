"""
Data normalization functions for scoring pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import logging

logger = logging.getLogger(__name__)


def normalize_min_max(series: pd.Series, feature_range: Tuple[float, float] = (0, 1)) -> Tuple[pd.Series, Dict]:
    """
    Min-Max normalization: scales values to a fixed range
    
    Args:
        series: Input data series
        feature_range: Target range for scaling
        
    Returns:
        Tuple of (normalized_series, normalization_params)
    """
    scaler = MinMaxScaler(feature_range=feature_range)
    
    # Handle edge case where all values are the same
    if series.nunique() <= 1:
        logger.warning(f"All values in series are the same ({series.iloc[0]}), returning zeros")
        normalized = pd.Series(np.zeros(len(series)), index=series.index)
        params = {'method': 'min_max', 'min_val': series.min(), 'max_val': series.max(), 'all_same': True}
        return normalized, params
    
    # Fit and transform
    values = series.values.reshape(-1, 1)
    normalized_values = scaler.fit_transform(values).flatten()
    normalized = pd.Series(normalized_values, index=series.index)
    
    params = {
        'method': 'min_max',
        'min_val': float(series.min()),
        'max_val': float(series.max()),
        'feature_range': feature_range,
        'all_same': False
    }
    
    return normalized, params


def normalize_z_score(series: pd.Series) -> Tuple[pd.Series, Dict]:
    """
    Z-score normalization: scales to mean=0, std=1
    
    Args:
        series: Input data series
        
    Returns:
        Tuple of (normalized_series, normalization_params)
    """
    mean_val = series.mean()
    std_val = series.std()
    
    # Handle edge case where std is 0
    if std_val == 0:
        logger.warning(f"Standard deviation is 0 for series (mean={mean_val}), returning zeros")
        normalized = pd.Series(np.zeros(len(series)), index=series.index)
        params = {'method': 'z_score', 'mean': mean_val, 'std': std_val, 'all_same': True}
        return normalized, params
    
    # Normalize
    normalized = (series - mean_val) / std_val
    
    params = {
        'method': 'z_score',
        'mean': float(mean_val),
        'std': float(std_val),
        'all_same': False
    }
    
    return normalized, params


def normalize_robust(series: pd.Series) -> Tuple[pd.Series, Dict]:
    """
    Robust normalization using median and IQR (less sensitive to outliers)
    
    Args:
        series: Input data series
        
    Returns:
        Tuple of (normalized_series, normalization_params)
    """
    median_val = series.median()
    q75 = series.quantile(0.75)
    q25 = series.quantile(0.25)
    iqr = q75 - q25
    
    # Handle edge case where IQR is 0
    if iqr == 0:
        logger.warning(f"IQR is 0 for series (median={median_val}), using fallback normalization")
        # Fallback to min-max if IQR is 0
        return normalize_min_max(series)
    
    # Normalize
    normalized = (series - median_val) / iqr
    
    params = {
        'method': 'robust',
        'median': float(median_val),
        'q25': float(q25),
        'q75': float(q75),
        'iqr': float(iqr)
    }
    
    return normalized, params


def normalize_campaign_metrics(
    df: pd.DataFrame, 
    method: str = 'min_max'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Normalize key campaign metrics for scoring
    
    Args:
        df: DataFrame with campaign metrics
        method: Normalization method ('min_max', 'z_score', 'robust')
        
    Returns:
        Tuple of (dataframe_with_normalized_columns, normalization_summary)
    """
    df = df.copy()
    
    # Metrics to normalize
    metrics_to_normalize = ['cpm', 'ctr', 'conversion_rate']
    
    # Track normalization parameters
    normalization_params = {}
    
    for metric in metrics_to_normalize:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found in dataframe, skipping")
            continue
            
        # Skip if all values are NaN
        if df[metric].isna().all():
            logger.warning(f"All values for '{metric}' are NaN, skipping")
            continue
            
        # Remove NaN values for normalization
        valid_data = df[metric].dropna()
        
        if len(valid_data) == 0:
            logger.warning(f"No valid data for '{metric}', skipping")
            continue
        
        # Apply normalization
        if method == 'min_max':
            normalized, params = normalize_min_max(valid_data)
        elif method == 'z_score':
            normalized, params = normalize_z_score(valid_data)
        elif method == 'robust':
            normalized, params = normalize_robust(valid_data)
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        # Create normalized column name
        normalized_col = f'{metric}_normalized'
        
        # Initialize normalized column with NaN
        df[normalized_col] = np.nan
        
        # Fill in normalized values where we have valid data
        df.loc[valid_data.index, normalized_col] = normalized
        
        # Store parameters
        normalization_params[metric] = params
        
        logger.info(f"Normalized '{metric}' using {method} method")
    
    # Create summary
    summary = {
        'method': method,
        'normalized_columns': list(normalization_params.keys()),
        'parameters': normalization_params,
        'rows_processed': len(df)
    }
    
    return df, summary


def handle_inverse_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle metrics where lower values are better (like CPM)
    by inverting their normalized values
    
    Args:
        df: DataFrame with normalized metrics
        
    Returns:
        DataFrame with inverse metrics adjusted
    """
    df = df.copy()
    
    # CPM is an inverse metric (lower is better)
    if 'cpm_normalized' in df.columns:
        # Invert CPM: new_value = 1 - normalized_value
        # This makes higher CPM result in lower scores
        df['cpm_normalized_inverted'] = 1 - df['cpm_normalized']
        
        # Handle NaN values
        df['cpm_normalized_inverted'] = df['cmp_normalized_inverted'].fillna(0)
        
        logger.info("Inverted CPM normalization (lower CPM now gives higher scores)")
    
    return df


def create_final_normalized_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Create final normalized features ready for scoring
    
    Args:
        df: DataFrame with normalized columns
        
    Returns:
        Tuple of (dataframe, list_of_feature_columns)
    """
    df = df.copy()
    
    # Handle inverse metrics
    df = handle_inverse_metrics(df)
    
    # Define final feature columns for scoring
    feature_columns = []
    
    # CTR (higher is better)
    if 'ctr_normalized' in df.columns:
        df['ctr_score_ready'] = df['ctr_normalized'].fillna(0)
        feature_columns.append('ctr_score_ready')
    
    # CPM (lower is better, use inverted)
    if 'cpm_normalized_inverted' in df.columns:
        df['cpm_score_ready'] = df['cpm_normalized_inverted'].fillna(0)
        feature_columns.append('cpm_score_ready')
    elif 'cpm_normalized' in df.columns:
        # Fallback if inversion failed
        df['cpm_score_ready'] = 1 - df['cpm_normalized'].fillna(1)
        feature_columns.append('cmp_score_ready')
    
    # Conversion Rate (higher is better)
    if 'conversion_rate_normalized' in df.columns:
        df['conversion_rate_score_ready'] = df['conversion_rate_normalized'].fillna(0)
        feature_columns.append('conversion_rate_score_ready')
    
    logger.info(f"Created {len(feature_columns)} normalized features for scoring: {feature_columns}")
    
    return df, feature_columns