"""
Data preprocessing for scoring pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def clean_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize column headers"""
    # Map common variations to standard names
    header_mapping = {
        # Domain variations
        'domain': 'domain', 'domains': 'domain', 'site': 'domain', 'website': 'domain',
        # Impressions variations  
        'impressions': 'impressions', 'impression': 'impressions', 'imps': 'impressions',
        'views': 'impressions', 'view': 'impressions',
        # CTR variations
        'ctr': 'ctr', 'click_through_rate': 'ctr', 'clickthrough_rate': 'ctr',
        'click_rate': 'ctr', 'clicks_per_impression': 'ctr',
        # Conversions variations
        'conversions': 'conversions', 'conversion': 'conversions', 'conv': 'conversions',
        'actions': 'conversions', 'action': 'conversions',
        # Spend variations
        'total_spend': 'total_spend', 'spend': 'total_spend', 'cost': 'total_spend',
        'total_cost': 'total_spend', 'budget': 'total_spend',
        # Publisher variations
        'publisher': 'publisher', 'pub': 'publisher', 'source': 'publisher',
        # CPM variations
        'cpm': 'cpm', 'cost_per_mille': 'cpm', 'cost_per_thousand': 'cpm',
        # Channel variations
        'channel': 'channel', 'media': 'channel', 'medium': 'channel',
        # Vendor variations
        'vendor': 'vendor', 'supplier': 'vendor', 'partner': 'vendor'
    }
    
    # Normalize column names (lowercase, strip spaces, replace special chars)
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_').str.replace('-', '_')
    
    # Apply mapping
    df = df.rename(columns=header_mapping)
    
    logger.info(f"Cleaned headers: {list(df.columns)}")
    return df


def validate_required_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that required columns are present"""
    required = ['domain', 'impressions', 'ctr', 'conversions', 'total_spend']
    missing = [col for col in required if col not in df.columns]
    
    is_valid = len(missing) == 0
    return is_valid, missing


def coerce_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns to appropriate data types"""
    df = df.copy()
    
    # Numeric columns
    numeric_columns = ['impressions', 'ctr', 'conversions', 'total_spend', 'cpm']
    for col in numeric_columns:
        if col in df.columns:
            # Remove percentage signs and convert
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '')
            
            # Convert to numeric, errors='coerce' will turn invalid values to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert CTR from percentage to decimal if needed
    if 'ctr' in df.columns and df['ctr'].max() > 1:
        df['ctr'] = df['ctr'] / 100
        logger.info("Converted CTR from percentage to decimal")
    
    # String columns
    string_columns = ['domain', 'publisher', 'channel', 'vendor']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    logger.info("Data types coerced successfully")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values appropriately"""
    df = df.copy()
    
    # Remove rows with missing required fields
    required_fields = ['domain', 'impressions', 'total_spend']
    initial_rows = len(df)
    df = df.dropna(subset=required_fields)
    removed_rows = initial_rows - len(df)
    
    if removed_rows > 0:
        logger.warning(f"Removed {removed_rows} rows due to missing required fields")
    
    # Fill missing CTR with 0
    if 'ctr' in df.columns:
        df['ctr'] = df['ctr'].fillna(0)
    
    # Fill missing conversions with 0
    if 'conversions' in df.columns:
        df['conversions'] = df['conversions'].fillna(0)
    
    # Fill missing optional fields
    if 'publisher' in df.columns:
        df['publisher'] = df['publisher'].fillna('Unknown')
    
    if 'channel' in df.columns:
        df['channel'] = df['channel'].fillna('Unknown')
    
    if 'vendor' in df.columns:
        df['vendor'] = df['vendor'].fillna('Unknown')
    
    return df


def derive_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived fields like CPM and conversion rate"""
    df = df.copy()
    
    # Calculate CPM if missing
    if 'cpm' not in df.columns or df['cpm'].isna().all():
        if 'total_spend' in df.columns and 'impressions' in df.columns:
            # CPM = (Total Spend / Impressions) * 1000
            df['cpm'] = np.where(
                df['impressions'] > 0,
                (df['total_spend'] / df['impressions']) * 1000,
                0
            )
            logger.info("Calculated CPM from total_spend and impressions")
    
    # Calculate conversion rate
    if 'conversion_rate' not in df.columns:
        if 'conversions' in df.columns and 'impressions' in df.columns:
            df['conversion_rate'] = np.where(
                df['impressions'] > 0,
                df['conversions'] / df['impressions'],
                0
            )
            logger.info("Calculated conversion_rate from conversions and impressions")
    
    # Calculate clicks if needed (for validation)
    if 'clicks' not in df.columns and 'ctr' in df.columns:
        df['clicks'] = df['impressions'] * df['ctr']
    
    return df


def remove_invalid_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with invalid data"""
    df = df.copy()
    initial_rows = len(df)
    
    # Remove rows with negative values where they shouldn't exist
    numeric_positive_cols = ['impressions', 'total_spend', 'cpm']
    for col in numeric_positive_cols:
        if col in df.columns:
            df = df[df[col] >= 0]
    
    # Remove rows with CTR > 100% (if still in percentage) or > 1 (if decimal)
    if 'ctr' in df.columns:
        df = df[df['ctr'] <= 1]
    
    # Remove rows with conversion rate > 100%
    if 'conversion_rate' in df.columns:
        df = df[df['conversion_rate'] <= 1]
    
    # Remove rows with zero impressions (can't calculate meaningful metrics)
    if 'impressions' in df.columns:
        df = df[df['impressions'] > 0]
    
    removed_rows = initial_rows - len(df)
    if removed_rows > 0:
        logger.warning(f"Removed {removed_rows} rows with invalid data")
    
    return df


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Complete preprocessing pipeline for campaign data
    
    Returns:
        Tuple of (processed_dataframe, preprocessing_summary)
    """
    logger.info(f"Starting preprocessing of {len(df)} rows")
    
    # Store original stats
    original_rows = len(df)
    original_cols = list(df.columns)
    
    # Step 1: Clean headers
    df = clean_headers(df)
    
    # Step 2: Validate required columns
    is_valid, missing_cols = validate_required_columns(df)
    if not is_valid:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Step 3: Coerce data types
    df = coerce_data_types(df)
    
    # Step 4: Handle missing values
    df = handle_missing_values(df)
    
    # Step 5: Derive calculated fields
    df = derive_calculated_fields(df)
    
    # Step 6: Remove invalid data
    df = remove_invalid_data(df)
    
    # Create summary
    summary = {
        'original_rows': original_rows,
        'processed_rows': len(df),
        'rows_removed': original_rows - len(df),
        'original_columns': original_cols,
        'processed_columns': list(df.columns),
        'data_quality': {
            'missing_ctr_filled': df['ctr'].isna().sum(),
            'missing_conversions_filled': df['conversions'].isna().sum(),
            'calculated_cpm': 'cpm' in df.columns,
            'calculated_conversion_rate': 'conversion_rate' in df.columns
        }
    }
    
    logger.info(f"Preprocessing completed: {len(df)} rows remaining")
    return df, summary