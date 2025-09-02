"""
Enhanced preprocessing implementing document-specific requirements
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedPreprocessor:
    """Enhanced preprocessing with document-specific logic"""
    
    def __init__(self):
        # Rows to exclude from scoring
        self.exclusion_patterns = [
            'row labels', 'grand total', 'tail aggregate', 'summary'
        ]
    
    def preprocess_for_scoring(self, df: pd.DataFrame, source: str, channel: str, 
                             analysis_level: str = 'Domain-level') -> Tuple[pd.DataFrame, Dict]:
        """
        Complete preprocessing pipeline implementing document requirements
        
        Args:
            df: Input DataFrame
            source: Data source ('TTD' or 'PulsePoint')
            channel: Channel type
            analysis_level: Analysis level ('Domain-level' or 'Supply Vendor-level')
            
        Returns:
            Tuple of (processed_dataframe, preprocessing_summary)
        """
        logger.info(f"Starting enhanced preprocessing for {source} {channel} at {analysis_level} level")
        
        original_rows = len(df)
        original_cols = list(df.columns)
        
        # Step 1: Clean and standardize headers
        df = self._clean_headers(df)
        
        # Step 2: Remove exclusion rows
        df = self._remove_exclusion_rows(df)
        
        # Step 3: Handle PulsePoint aggregation if needed
        if source == 'PulsePoint':
            df = self._handle_pulsepoint_aggregation(df, channel)
        
        # Step 4: Derive calculated fields
        df = self._derive_calculated_fields(df, source, channel)
        
        # Step 5: Handle analysis level grouping
        df = self._handle_analysis_level(df, source, channel, analysis_level)
        
        # Step 6: Validate minimum thresholds
        df = self._apply_minimum_thresholds(df, source)
        
        # Step 7: Final data cleaning
        df = self._final_data_cleaning(df)
        
        # Create summary
        summary = {
            'original_rows': original_rows,
            'processed_rows': len(df),
            'rows_removed': original_rows - len(df),
            'original_columns': original_cols,
            'processed_columns': list(df.columns),
            'source': source,
            'channel': channel,
            'analysis_level': analysis_level,
            'exclusions_applied': {
                'exclusion_rows_removed': original_rows - len(df),
                'exclusion_patterns': self.exclusion_patterns
            }
        }
        
        logger.info(f"Enhanced preprocessing completed: {len(df)} rows remaining")
        return df, summary
    
    def _clean_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column headers"""
        df_clean = df.copy()
        
        # Map common variations to standard names
        header_mapping = {
            # Domain/Site variations
            'domain': 'domain', 'domains': 'domain', 'site': 'domain', 'website': 'domain',
            'app': 'app_name', 'application': 'app_name',  # Keep app names separate for mobile
            
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
            'total_cost': 'total_spend', 'budget': 'total_spend', 'advertiser_cost': 'advertiser_cost',
            
            # Publisher/SSP variations
            'publisher': 'publisher', 'pub': 'publisher', 'source': 'publisher',
            'supply_vendor': 'supply_vendor', 'vendor': 'supply_vendor', 'ssp': 'supply_vendor',
            
            # CPM variations
            'cpm': 'cpm', 'cost_per_mille': 'cpm', 'cost_per_thousand': 'cpm',
            'ecpm': 'ecpm', 'effective_cpm': 'ecpm',
            
            # Channel variations
            'channel': 'channel', 'media': 'channel', 'medium': 'channel',
            
            # TTD specific
            'ias_display_fully_in_view_1s': 'ias_display_fully_in_view_1s',
            'ad_load_xl_imps': 'ad_load_xl_imps', 'ad_refresh_15s_imps': 'ad_refresh_15s_imps',
            'all_last_click_view_conversion_rate': 'all_last_click_view_conversion_rate',
            'sampled_in_view': 'sampled_in_view',
            'player_completion': 'player_completion',
            'player_errors': 'player_errors',
            'player_mute': 'player_mute',
            'tv_quality_index_raw': 'tv_quality_index_raw',
            'tv_quality_index_measured': 'tv_quality_index_measured',
            'unique_ids': 'unique_ids',
            
            # PulsePoint specific
            'completion_rate': 'completion_rate'
        }
        
        # Normalize column names first
        df_clean.columns = df_clean.columns.str.lower().str.strip().str.replace(' ', '_').str.replace('-', '_').str.replace('(', '').str.replace(')', '')
        
        # Apply mapping
        df_clean = df_clean.rename(columns=header_mapping)
        
        logger.info(f"Cleaned headers: {list(df_clean.columns)}")
        return df_clean
    
    def _remove_exclusion_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows matching exclusion patterns"""
        df_clean = df.copy()
        initial_rows = len(df_clean)
        
        # Create exclusion mask
        exclusion_mask = pd.Series(False, index=df_clean.index)
        
        # Only check the first column (identifier column) for exclusion patterns
        # This prevents matching patterns in data columns
        if len(df_clean.columns) > 0:
            first_col = df_clean.columns[0]
            logger.info(f"Checking exclusion patterns in first column: {first_col}")
            logger.info(f"First column values: {df_clean[first_col].tolist()}")
            
            if df_clean[first_col].dtype == 'object':
                for pattern in self.exclusion_patterns:
                    logger.info(f"Checking pattern: '{pattern}'")
                    # Use exact matching instead of regex to avoid false positives
                    mask = df_clean[first_col].astype(str).str.lower() == pattern.lower()
                    logger.info(f"Pattern '{pattern}' matched rows: {mask.sum()}")
                    exclusion_mask |= mask
        
        # Remove excluded rows
        df_clean = df_clean[~exclusion_mask]
        
        removed_rows = initial_rows - len(df_clean)
        if removed_rows > 0:
            logger.info(f"Removed {removed_rows} rows matching exclusion patterns")
        
        return df_clean
    
    def _handle_pulsepoint_aggregation(self, df: pd.DataFrame, channel: str) -> pd.DataFrame:
        """Handle PulsePoint domain aggregation as per document requirements"""
        df_agg = df.copy()
        
        # Check if we need to aggregate by domain (ignore publisher)
        if 'publisher' in df_agg.columns and 'domain' in df_agg.columns:
            logger.info("Applying PulsePoint domain aggregation (ignoring publisher)")
            
            # Group by domain and aggregate metrics
            agg_functions = {
                'impressions': 'sum',
                'total_spend': 'sum',
                'conversions': 'sum'
            }
            
            # Add channel-specific aggregations
            if channel == 'video' and 'completion_rate' in df_agg.columns:
                # Weighted completion rate for video
                agg_functions['completion_rate'] = lambda x: np.average(x, weights=df_agg.loc[x.index, 'impressions'])
            
            # Aggregate
            df_agg = df_agg.groupby('domain').agg(agg_functions).reset_index()
            
            # Recalculate KPIs after aggregation
            df_agg = self._recalculate_pulsepoint_kpis(df_agg, channel)
            
            logger.info(f"Aggregated to {len(df_agg)} unique domains")
        
        return df_agg
    
    def _recalculate_pulsepoint_kpis(self, df: pd.DataFrame, channel: str) -> pd.DataFrame:
        """Recalculate KPIs after PulsePoint aggregation"""
        df_calc = df.copy()
        
        # Calculate eCPM = (Total Spend / Impressions) * 1000
        if 'total_spend' in df_calc.columns and 'impressions' in df_calc.columns:
            df_calc['ecpm'] = np.where(
                df_calc['impressions'] > 0,
                (df_calc['total_spend'] / df_calc['impressions']) * 1000,
                0
            )
        
        # Calculate conversion rate
        if 'conversions' in df_calc.columns and 'impressions' in df_calc.columns:
            df_calc['conversion_rate'] = np.where(
                df_calc['impressions'] > 0,
                df_calc['conversions'] / df_calc['impressions'],
                0
            )
        
        # Calculate CTR if not present
        if 'ctr' not in df_calc.columns and 'clicks' in df_calc.columns:
            df_calc['ctr'] = np.where(
                df_calc['impressions'] > 0,
                df_calc['clicks'] / df_calc['impressions'],
                0
            )
        
        logger.info("Recalculated PulsePoint KPIs after aggregation")
        return df_calc
    
    def _derive_calculated_fields(self, df: pd.DataFrame, source: str, channel: str) -> pd.DataFrame:
        """Derive calculated fields as per document requirements"""
        df_calc = df.copy()
        
        if source == 'TTD':
            # TTD Display specific calculations
            if channel == 'display':
                # Ad Load Rate = Load Imps / Imps
                if 'ad_load_xl_imps' in df_calc.columns and 'impressions' in df_calc.columns:
                    df_calc['ad_load_rate'] = np.where(
                        df_calc['impressions'] > 0,
                        df_calc['ad_load_xl_imps'] / df_calc['impressions'],
                        0
                    )
                
                # Ad Refresh Rate = Refresh Imps / Imps
                if 'ad_refresh_15s_imps' in df_calc.columns and 'impressions' in df_calc.columns:
                    df_calc['ad_refresh_rate'] = np.where(
                        df_calc['impressions'] > 0,
                        df_calc['ad_refresh_15s_imps'] / df_calc['impressions'],
                        0
                    )
            
            # TTD CTV specific calculations
            elif channel == 'ctv':
                # TVQI ratio = TVQI Raw / TVQI Measured
                if 'tv_quality_index_raw' in df_calc.columns and 'tv_quality_index_measured' in df_calc.columns:
                    df_calc['tv_quality_index_ratio'] = np.where(
                        df_calc['tv_quality_index_measured'] > 0,
                        df_calc['tv_quality_index_raw'] / df_calc['tv_quality_index_measured'],
                        0
                    )
                
                # Unique ID Ratio = Unique IDs / Impressions
                if 'unique_ids' in df_calc.columns and 'impressions' in df_calc.columns:
                    df_calc['unique_id_ratio'] = np.where(
                        df_calc['impressions'] > 0,
                        df_calc['unique_ids'] / df_calc['impressions'],
                        0
                    )
        
        elif source == 'PulsePoint':
            # Calculate eCPM if missing
            if 'ecpm' not in df_calc.columns and 'total_spend' in df_calc.columns and 'impressions' in df_calc.columns:
                df_calc['ecpm'] = np.where(
                    df_calc['impressions'] > 0,
                    (df_calc['total_spend'] / df_calc['impressions']) * 1000,
                    0
                )
            
            # Calculate conversion rate if missing
            if 'conversion_rate' not in df_calc.columns and 'conversions' in df_calc.columns and 'impressions' in df_calc.columns:
                df_calc['conversion_rate'] = np.where(
                    df_calc['impressions'] > 0,
                    df_calc['conversions'] / df_calc['impressions'],
                    0
                )
        
        logger.info(f"Derived calculated fields for {source} {channel}")
        return df_calc
    
    def _handle_analysis_level(self, df: pd.DataFrame, source: str, channel: str, 
                              analysis_level: str) -> pd.DataFrame:
        """Handle analysis level grouping"""
        df_level = df.copy()
        
        if analysis_level == 'Supply Vendor-level' and 'supply_vendor' in df_level.columns:
            # Group by supply vendor for TTD
            if source == 'TTD':
                logger.info("Grouping by supply vendor for TTD analysis")
                agg_functions = {
                    'impressions': 'sum',
                    'advertiser_cost': 'sum'
                }
                
                # Add other metrics that can be summed
                summable_cols = ['clicks', 'conversions', 'ad_load_xl_imps', 'ad_refresh_15s_imps']
                for col in summable_cols:
                    if col in df_level.columns:
                        agg_functions[col] = 'sum'
                
                # Group and aggregate
                df_level = df_level.groupby('supply_vendor').agg(agg_functions).reset_index()
                
                # Recalculate derived metrics after grouping
                df_level = self._recalculate_after_grouping(df_level, source, channel)
        
        return df_level
    
    def _recalculate_after_grouping(self, df: pd.DataFrame, source: str, channel: str) -> pd.DataFrame:
        """Recalculate metrics after grouping operations"""
        df_calc = df.copy()
        
        if source == 'TTD':
            if channel == 'display':
                # Recalculate rates after grouping
                if 'ad_load_rate' in df_calc.columns and 'impressions' in df_calc.columns:
                    df_calc['ad_load_rate'] = np.where(
                        df_calc['impressions'] > 0,
                        df_calc['ad_load_xl_imps'] / df_calc['impressions'],
                        0
                    )
                
                if 'ad_refresh_rate' in df_calc.columns and 'impressions' in df_calc.columns:
                    df_calc['ad_refresh_rate'] = np.where(
                        df_calc['impressions'] > 0,
                        df_calc['ad_refresh_15s_imps'] / df_calc['impressions'],
                        0
                    )
        
        return df_calc
    
    def _apply_minimum_thresholds(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Apply minimum thresholds as per document requirements"""
        df_thresh = df.copy()
        initial_rows = len(df_thresh)
        
        if source == 'PulsePoint':
            # Require ≥ 0.05% of total impressions
            if 'impressions' in df_thresh.columns:
                total_impressions = df_thresh['impressions'].sum()
                min_impressions = total_impressions * 0.0005
                df_thresh = df_thresh[df_thresh['impressions'] >= min_impressions]
        
        elif source == 'TTD':
            # Require ≥ 250 impressions for display/video, but lower for mobile apps
            if 'impressions' in df_thresh.columns:
                # Check if this is a mobile app file (has app_name column)
                if 'app_name' in df_thresh.columns:
                    # Mobile apps can have lower thresholds
                    df_thresh = df_thresh[df_thresh['impressions'] >= 10]  # Lower threshold for mobile
                    logger.info("Applied mobile app threshold: ≥ 10 impressions")
                else:
                    # Standard TTD threshold
                    df_thresh = df_thresh[df_thresh['impressions'] >= 250]
                    logger.info("Applied standard TTD threshold: ≥ 250 impressions")
        
        removed_rows = initial_rows - len(df_thresh)
        if removed_rows > 0:
            logger.info(f"Removed {removed_rows} rows below minimum thresholds")
        
        return df_thresh
    
    def _final_data_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final data cleaning and validation"""
        df_clean = df.copy()
        initial_rows = len(df_clean)
        
        # Remove rows with negative values where they shouldn't exist
        numeric_positive_cols = ['impressions', 'total_spend', 'advertiser_cost', 'cpm', 'ecpm']
        for col in numeric_positive_cols:
            if col in df_clean.columns:
                df_clean = df_clean[df_clean[col] >= 0]
        
        # Remove rows with invalid rates (> 100% or > 1)
        rate_cols = ['ctr', 'conversion_rate', 'completion_rate', 'ad_load_rate', 'ad_refresh_rate']
        for col in rate_cols:
            if col in df_clean.columns:
                df_clean = df_clean[df_clean[col] <= 1]
        
        # Remove rows with zero impressions
        if 'impressions' in df_clean.columns:
            df_clean = df_clean[df_clean['impressions'] > 0]
        
        removed_rows = initial_rows - len(df_clean)
        if removed_rows > 0:
            logger.info(f"Removed {removed_rows} rows in final data cleaning")
        
        return df_clean
