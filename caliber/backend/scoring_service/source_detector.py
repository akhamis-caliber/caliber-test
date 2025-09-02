"""
Source detection for PulsePoint vs TTD data sources
"""

import pandas as pd
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class SourceDetector:
    """Detects and validates data source (PulsePoint vs TTD)"""
    
    # PulsePoint specific columns
    PULSEPOINT_COLUMNS = {
        'display': ['domain', 'total_spend', 'impressions', 'ecpm', 'ctr', 'conversions'],
        'video': ['domain', 'total_spend', 'impressions', 'ecpm', 'ctr', 'completion_rate', 'conversions']
    }
    
    # TTD specific columns
    TTD_COLUMNS = {
        'display': ['site', 'supply_vendor', 'advertiser_cost', 'impressions', 'cpm', 'clicks', 'ctr', 
                   'ias_display_fully_in_view_1s', 'ad_load_xl_imps', 'ad_refresh_15s_imps', 
                   'all_last_click_view_conversion_rate'],
        'video': ['site', 'supply_vendor', 'advertiser_cost', 'impressions', 'cpm', 'sampled_in_view', 
                 'player_completion', 'player_errors', 'player_mute'],
        'video_mobile': ['site', 'app', 'impressions', 'advertiser_cost', 'player_errors', 'player_mute',
                        'sampled_tracked_impressions', 'sampled_viewed_impressions', 'player_completed_views', 'player_starts'],
        'audio': ['site', 'supply_vendor', 'advertiser_cost', 'impressions', 'cpm', 'sampled_in_view', 
                 'player_completion', 'player_errors', 'player_mute'],
        'ctv': ['supply_vendor', 'advertiser_cost', 'impressions', 'tv_quality_index_raw', 
                'tv_quality_index_measured', 'unique_ids']
    }
    
    def __init__(self):
        self.detected_source = None
        self.detected_channel = None
        self.validation_errors = []
    
    def detect_source(self, df: pd.DataFrame) -> Tuple[str, str, Dict]:
        """
        Auto-detect data source and channel
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (source, channel, detection_summary)
        """
        logger.info("Starting source detection...")
        
        # Clean column names for detection
        df_clean = self._clean_columns_for_detection(df)
        
        # Try to detect TTD first (more specific columns)
        ttd_result = self._detect_ttd(df_clean)
        if ttd_result['detected']:
            self.detected_source = 'TTD'
            self.detected_channel = ttd_result['channel']
            logger.info(f"Detected TTD {ttd_result['channel']} source")
            return 'TTD', ttd_result['channel'], ttd_result
        
        # Try to detect PulsePoint
        pulsepoint_result = self._detect_pulsepoint(df_clean)
        if pulsepoint_result['detected']:
            self.detected_source = 'PulsePoint'
            self.detected_channel = pulsepoint_result['channel']
            logger.info(f"Detected PulsePoint {pulsepoint_result['channel']} source")
            return 'PulsePoint', pulsepoint_result['channel'], pulsepoint_result
        
        # Unknown source
        logger.warning("Could not determine data source")
        return 'Unknown', 'Unknown', {
            'detected': False,
            'confidence': 0.0,
            'available_columns': list(df_clean.columns),
            'errors': ['No recognizable column pattern found']
        }
    
    def _clean_columns_for_detection(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean column names for detection"""
        df_clean = df.copy()
        df_clean.columns = df_clean.columns.str.lower().str.strip().str.replace(' ', '_').str.replace('-', '_')
        return df_clean
    
    def _detect_ttd(self, df: pd.DataFrame) -> Dict:
        """Detect TTD source and channel"""
        available_cols = set(df.columns)
        
        # Check each TTD channel
        for channel, required_cols in self.TTD_COLUMNS.items():
            # Count matching columns
            matching_cols = [col for col in required_cols if col in available_cols]
            match_ratio = len(matching_cols) / len(required_cols)
            
            if match_ratio >= 0.6:  # At least 60% of required columns present
                # Additional validation for specific channels
                if channel == 'display':
                    # Must have site and supply_vendor
                    if 'site' in available_cols and 'supply_vendor' in available_cols:
                        return {
                            'detected': True,
                            'channel': channel,
                            'confidence': match_ratio,
                            'matching_columns': matching_cols,
                            'missing_columns': [col for col in required_cols if col not in available_cols],
                            'source': 'TTD'
                        }
                elif channel == 'video' or channel == 'audio':
                    if 'site' in available_cols and 'supply_vendor' in available_cols:
                        return {
                            'detected': True,
                            'channel': channel,
                            'confidence': match_ratio,
                            'matching_columns': matching_cols,
                            'missing_columns': [col for col in required_cols if col not in available_cols],
                            'source': 'TTD'
                        }
                elif channel == 'video_mobile':
                    if 'site' in available_cols and 'app' in available_cols:
                        return {
                            'detected': True,
                            'channel': channel,
                            'confidence': match_ratio,
                            'matching_columns': matching_cols,
                            'missing_columns': [col for col in required_cols if col not in available_cols],
                            'source': 'TTD'
                        }
                elif channel == 'ctv':
                    if 'supply_vendor' in available_cols:
                        return {
                            'detected': True,
                            'channel': channel,
                            'confidence': match_ratio,
                            'matching_columns': matching_cols,
                            'missing_columns': [col for col in required_cols if col not in available_cols],
                            'source': 'TTD'
                        }
        
        return {'detected': False, 'confidence': 0.0}
    
    def _detect_pulsepoint(self, df: pd.DataFrame) -> Dict:
        """Detect PulsePoint source and channel"""
        available_cols = set(df.columns)
        
        # Check each PulsePoint channel
        for channel, required_cols in self.PULSEPOINT_COLUMNS.items():
            # Count matching columns
            matching_cols = [col for col in required_cols if col in available_cols]
            match_ratio = len(matching_cols) / len(required_cols)
            
            if match_ratio >= 0.7:  # At least 70% of required columns present
                # Must have domain for PulsePoint
                if 'domain' in available_cols:
                    return {
                        'detected': True,
                        'channel': channel,
                        'confidence': match_ratio,
                        'matching_columns': matching_cols,
                        'missing_columns': [col for col in required_cols if col not in available_cols],
                        'source': 'PulsePoint'
                    }
        
        return {'detected': False, 'confidence': 0.0}
    
    def validate_required_inputs(self, df: pd.DataFrame, source: str, channel: str, goal: str, ctr_sensitive: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate required inputs based on source, channel, and goal
        
        Args:
            df: Input DataFrame
            source: Data source ('TTD' or 'PulsePoint')
            channel: Channel type
            goal: Campaign goal ('Awareness' or 'Action')
            ctr_sensitive: Whether CTR sensitivity applies
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        logger.info(f"Validating required inputs for {source} {channel} {goal} goal")
        
        missing_fields = []
        available_cols = set(df.columns)
        required_fields = []  # Initialize required_fields
        
        # Create column name variations mapping for validation
        column_variations = {
            # PulsePoint variations
            'domain': ['Domain', 'domain', 'domains', 'Domains'],
            'total_spend': ['Total Spend', 'total_spend', 'TotalSpend', 'totalSpend'],
            'impressions': ['Impressions', 'impressions', 'Imps', 'imps'],
            'ecpm': ['eCPM', 'ecpm', 'ECPM', 'effective_cpm'],
            'ctr': ['CTR', 'ctr', 'Click Through Rate', 'click_through_rate'],
            'conversions': ['Conversions', 'conversions', 'Conversions', 'conv'],
            'completion_rate': ['Completion Rate', 'completion_rate', 'CompletionRate'],
            
            # TTD variations
            'site': ['Site', 'site', 'Website', 'website'],
            'app': ['App', 'app', 'Application', 'application'],
            'supply_vendor': ['Supply Vendor', 'supply_vendor', 'SupplyVendor', 'SSP', 'ssp'],
            'advertiser_cost': ['Advertiser Cost', 'advertiser_cost', 'AdvertiserCost', 'Cost', 'cost'],
            'cpm': ['CPM', 'cpm', 'Cost Per Mille', 'cost_per_mille'],
            'clicks': ['Clicks', 'clicks', 'Click', 'click'],
            'ias_display_fully_in_view_1s': ['IAS Display Fully In View 1s', 'ias_display_fully_in_view_1s'],
            'ad_load_xl_imps': ['Ad Load – XL (Imps)', 'ad_load_xl_imps', 'Ad Load XL Imps'],
            'ad_refresh_15s_imps': ['Ad Refresh <15s (Imps)', 'ad_refresh_15s_imps', 'Ad Refresh 15s Imps'],
            'all_last_click_view_conversion_rate': ['All Last Click + View Conversion Rate', 'all_last_click_view_conversion_rate'],
            'sampled_in_view': ['Sampled In-View', 'sampled_in_view', 'SampledInView'],
            'player_completion': ['Player Completion', 'player_completion', 'PlayerCompletion'],
            'player_errors': ['Player Errors', 'player_errors', 'PlayerErrors'],
            'player_mute': ['Player Mute', 'player_mute', 'PlayerMute'],
            'sampled_tracked_impressions': ['Sampled Tracked Impressions', 'sampled_tracked_impressions', 'SampledTrackedImpressions'],
            'sampled_viewed_impressions': ['Sampled Viewed Impressions', 'sampled_viewed_impressions', 'SampledViewedImpressions'],
            'player_completed_views': ['Player Completed Views', 'player_completed_views', 'PlayerCompletedViews'],
            'player_starts': ['Player Starts', 'player_starts', 'PlayerStarts'],
            'tv_quality_index_raw': ['TV Quality Index (Raw)', 'tv_quality_index_raw', 'TVQualityIndexRaw'],
            'tv_quality_index_measured': ['TV Quality Index (Measured)', 'tv_quality_index_measured', 'TVQualityIndexMeasured'],
            'unique_ids': ['Unique IDs', 'unique_ids', 'UniqueIDs']
        }
        
        if source == 'TTD':
            if channel == 'display':
                required_fields = ['site', 'supply_vendor', 'advertiser_cost', 'impressions', 'cpm']
                if goal == 'Awareness':
                    if ctr_sensitive:
                        required_fields.extend(['clicks', 'ctr', 'ias_display_fully_in_view_1s', 
                                             'ad_load_xl_imps', 'ad_refresh_15s_imps'])
                    else:
                        required_fields.extend(['ias_display_fully_in_view_1s', 'ad_load_xl_imps', 
                                             'ad_refresh_15s_imps'])
                else:  # Action
                    required_fields.extend(['clicks', 'ctr', 'all_last_click_view_conversion_rate', 
                                         'ad_load_xl_imps', 'ad_refresh_15s_imps'])
            
            elif channel in ['video', 'audio']:
                required_fields = ['site', 'supply_vendor', 'advertiser_cost', 'impressions', 'cpm', 
                                 'sampled_in_view', 'player_completion', 'player_errors', 'player_mute']
            
            elif channel == 'video_mobile':
                required_fields = ['site', 'app', 'impressions', 'advertiser_cost', 'player_errors', 'player_mute',
                                 'sampled_tracked_impressions', 'sampled_viewed_impressions', 'player_completed_views', 'player_starts']
            
            elif channel == 'ctv':
                required_fields = ['supply_vendor', 'advertiser_cost', 'impressions', 
                                 'tv_quality_index_raw', 'tv_quality_index_measured', 'unique_ids']
        
        elif source == 'PulsePoint':
            if channel == 'display':
                required_fields = ['domain', 'total_spend', 'impressions', 'ecpm', 'ctr', 'conversions']
            elif channel == 'video':
                required_fields = ['domain', 'total_spend', 'impressions', 'ecpm', 'ctr', 'completion_rate', 'conversions']
        
        # Check for missing required fields with column name variations
        for field in required_fields:
            field_found = False
            if field in available_cols:
                field_found = True
            else:
                # Check variations
                variations = column_variations.get(field, [])
                for variation in variations:
                    if variation in available_cols:
                        field_found = True
                        break
            
            if not field_found:
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        
        if not is_valid:
            logger.error(f"Missing required fields for {source} {channel} {goal}: {missing_fields}")
        else:
            logger.info(f"All required fields present for {source} {channel} {goal}")
        
        return is_valid, missing_fields
    
    def get_analysis_level_options(self, source: str, channel: str) -> List[str]:
        """Get available analysis levels for the source/channel combination"""
        if source == 'TTD':
            if channel == 'display':
                return ['Domain-level', 'Supply Vendor-level']
            elif channel in ['video', 'audio']:
                return ['Domain-level', 'Supply Vendor-level']
            elif channel == 'video_mobile':
                return ['Domain-level', 'Supply Vendor-level']
            elif channel == 'ctv':
                return ['Supply Vendor-level']  # CTV typically vendor-focused
        elif source == 'PulsePoint':
            return ['Domain-level']  # PulsePoint is domain-focused
        
        return ['Domain-level']  # Default fallback
