import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from pathlib import Path
import re

from scoring_service.config import ScoringConfig, COLUMN_MAPPINGS
from common.exceptions import ValidationError

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Handles data cleaning, validation, and preparation for scoring"""
    
    def __init__(self, config: ScoringConfig):
        self.config = config
        self.column_mapping = {}
        self.data_quality_issues = []
    
    def process_file(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main preprocessing pipeline
        Returns: (processed_dataframe, processing_report)
        """
        logger.info(f"Starting data preprocessing for {len(df)} rows")
        
        processing_report = {
            "original_rows": len(df),
            "original_columns": list(df.columns),
            "data_quality_issues": [],
            "column_mapping": {},
            "final_rows": 0,
            "excluded_rows": [],
            "derived_metrics": []
        }
        
        try:
            # Step 1: Clean and standardize column names
            df = self._clean_column_names(df)
            
            # Step 2: Map columns to standard names
            df, column_mapping = self._map_columns(df)
            processing_report["column_mapping"] = column_mapping
            self.column_mapping = column_mapping
            
            # Step 3: Validate required columns exist
            self._validate_required_columns(df)
            
            # Step 4: Remove aggregate/total rows
            df, excluded_rows = self._remove_aggregate_rows(df)
            processing_report["excluded_rows"] = excluded_rows
            
            # Step 5: Clean and validate data types
            df = self._clean_data_types(df)
            
            # Step 6: Calculate derived metrics
            df, derived_metrics = self._calculate_derived_metrics(df)
            processing_report["derived_metrics"] = derived_metrics
            
            # Step 7: Apply platform-specific aggregation (PulsePoint domain-level)
            if self.config.platform.value == "pulsepoint":
                df = self._aggregate_by_domain(df)
            
            # Step 8: Filter minimum volume requirements
            df = self._apply_volume_filters(df)
            
            # Step 9: Data quality validation
            self._validate_data_quality(df)
            
            processing_report["final_rows"] = len(df)
            processing_report["data_quality_issues"] = self.data_quality_issues
            
            logger.info(f"Preprocessing complete: {len(df)} rows remaining")
            return df, processing_report
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise ValidationError(f"Data preprocessing failed: {str(e)}")
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column names"""
        # Remove extra whitespace and normalize case
        df.columns = [col.strip() for col in df.columns]
        
        # Remove common prefixes/suffixes that might interfere
        cleaned_columns = []
        for col in df.columns:
            # Remove common report prefixes
            col = re.sub(r'^(TTD_|PulsePoint_|Report_)', '', col, flags=re.IGNORECASE)
            cleaned_columns.append(col)
        
        df.columns = cleaned_columns
        return df
    
    def _map_columns(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Map DataFrame columns to standardized names"""
        column_mapping = {}
        df_columns = list(df.columns)
        df_columns_lower = [col.lower().replace('_', ' ').replace('-', ' ') for col in df_columns]
        
        for standard_name, variations in COLUMN_MAPPINGS.items():
            mapped_column = None
            
            # Try exact matches first
            for i, df_col in enumerate(df_columns):
                if df_col in variations:
                    mapped_column = df_col
                    break
            
            # Try fuzzy matches
            if not mapped_column:
                for i, df_col_lower in enumerate(df_columns_lower):
                    for variation in variations:
                        variation_lower = variation.lower().replace('_', ' ').replace('-', ' ')
                        if self._fuzzy_match(df_col_lower, variation_lower):
                            mapped_column = df_columns[i]
                            break
                    if mapped_column:
                        break
            
            if mapped_column:
                column_mapping[standard_name] = mapped_column
                # Rename column in DataFrame
                df = df.rename(columns={mapped_column: standard_name})
        
        return df, column_mapping
    
    def _fuzzy_match(self, col1: str, col2: str, threshold: float = 0.8) -> bool:
        """Check if two column names are similar enough"""
        # Simple fuzzy matching - can be enhanced with libraries like fuzzywuzzy
        col1_words = set(col1.split())
        col2_words = set(col2.split())
        
        if not col1_words or not col2_words:
            return False
        
        intersection = col1_words.intersection(col2_words)
        union = col1_words.union(col2_words)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def _validate_required_columns(self, df: pd.DataFrame):
        """Ensure all required columns are present"""
        missing_columns = []
        
        # Check for required columns based on configuration
        for metric in self.config.metrics:
            if metric.required and metric.name not in df.columns:
                missing_columns.append(metric.name)
        
        # Check for dimension columns
        if self.config.analysis_level == "domain" and "domain" not in df.columns:
            missing_columns.append("domain")
        elif self.config.analysis_level == "supply_vendor" and "supply_vendor" not in df.columns:
            missing_columns.append("supply_vendor")
        
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
    
    def _remove_aggregate_rows(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Remove aggregate/total rows that shouldn't be scored"""
        excluded_rows = []
        initial_count = len(df)
        
        # Identify dimension column
        dimension_col = "domain" if "domain" in df.columns else "supply_vendor"
        
        if dimension_col in df.columns:
            # Remove rows with aggregate indicators
            aggregate_indicators = [
                '[tail aggregate]', 'grand total', 'total', 'row labels',
                'summary', 'aggregate', '(not set)', '(not available)'
            ]
            
            mask = pd.Series([True] * len(df))
            for indicator in aggregate_indicators:
                indicator_mask = df[dimension_col].astype(str).str.lower().str.contains(
                    indicator.lower(), na=False
                )
                excluded_rows.extend(
                    df[indicator_mask][dimension_col].astype(str).tolist()
                )
                mask &= ~indicator_mask
            
            df = df[mask].reset_index(drop=True)
        
        logger.info(f"Removed {initial_count - len(df)} aggregate rows")
        return df, excluded_rows
    
    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types"""
        
        # Convert numeric columns
        numeric_columns = ["impressions", "clicks", "conversions", "total_spend", "advertiser_cost"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert percentage columns (might be in 0-100 or 0-1 format)
        percentage_columns = ["ctr", "conversion_rate", "completion_rate", "sampled_in_view_rate"]
        for col in percentage_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Detect if percentages are in 0-100 format and convert to 0-1
                if df[col].max() > 1:
                    df[col] = df[col] / 100
        
        # Remove rows with critical missing values
        critical_columns = ["impressions"]
        if self.config.analysis_level == "domain":
            critical_columns.append("domain")
        else:
            critical_columns.append("supply_vendor")
        
        for col in critical_columns:
            if col in df.columns:
                before_count = len(df)
                df = df.dropna(subset=[col])
                after_count = len(df)
                if before_count != after_count:
                    self.data_quality_issues.append(
                        f"Removed {before_count - after_count} rows with missing {col}"
                    )
        
        return df
    
    def _calculate_derived_metrics(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Calculate derived metrics based on platform requirements"""
        derived_metrics = []
        
        # Calculate CPM/eCPM
        if "total_spend" in df.columns and "impressions" in df.columns:
            df["cpm"] = (df["total_spend"] / df["impressions"]) * 1000
            df["ecpm"] = df["cpm"]  # Alias for PulsePoint
            derived_metrics.append("cpm/ecpm")
        elif "advertiser_cost" in df.columns and "impressions" in df.columns:
            df["cpm"] = (df["advertiser_cost"] / df["impressions"]) * 1000
            derived_metrics.append("cpm")
        
        # Calculate conversion rate
        if "conversions" in df.columns and "impressions" in df.columns:
            df["conversion_rate"] = df["conversions"] / df["impressions"]
            derived_metrics.append("conversion_rate")
        
        # Calculate CTR (if not already present)
        if "clicks" in df.columns and "impressions" in df.columns and "ctr" not in df.columns:
            df["ctr"] = df["clicks"] / df["impressions"]
            derived_metrics.append("ctr")
        
        # Trade Desk specific rates
        if self.config.platform.value == "trade_desk":
            # Ad Load rate
            if "ad_load_xl_rate" not in df.columns and "ad_load_xl_impressions" in df.columns:
                df["ad_load_xl_rate"] = df["ad_load_xl_impressions"] / df["impressions"]
                derived_metrics.append("ad_load_xl_rate")
            
            # Ad Refresh rate
            if "ad_refresh_below_15s_rate" not in df.columns and "ad_refresh_below_15s_impressions" in df.columns:
                df["ad_refresh_below_15s_rate"] = df["ad_refresh_below_15s_impressions"] / df["impressions"]
                derived_metrics.append("ad_refresh_below_15s_rate")
            
            # TV Quality Index rate (for CTV)
            if ("tv_quality_index_rate" not in df.columns and 
                "tv_quality_index" in df.columns and 
                "tv_quality_index_measured_impressions" in df.columns):
                df["tv_quality_index_rate"] = (
                    df["tv_quality_index"] / df["tv_quality_index_measured_impressions"]
                )
                derived_metrics.append("tv_quality_index_rate")
            
            # Unique ID ratio (for CTV)
            if "unique_id_ratio" not in df.columns and "unique_ids" in df.columns:
                df["unique_id_ratio"] = df["unique_ids"] / df["impressions"]
                derived_metrics.append("unique_id_ratio")
            
            # Player error/mute rates
            if "player_errors_rate" not in df.columns and "player_errors" in df.columns:
                df["player_errors_rate"] = df["player_errors"] / df["impressions"]
                derived_metrics.append("player_errors_rate")
            
            if "player_mute_rate" not in df.columns and "player_mute" in df.columns:
                df["player_mute_rate"] = df["player_mute"] / df["impressions"]
                derived_metrics.append("player_mute_rate")
        
        return df, derived_metrics
    
    def _aggregate_by_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate data by domain for PulsePoint (as per requirements)"""
        if "domain" not in df.columns:
            return df
        
        logger.info("Aggregating PulsePoint data by domain")
        
        # Define aggregation methods
        agg_methods = {
            "impressions": "sum",
            "total_spend": "sum",
            "clicks": "sum" if "clicks" in df.columns else None,
            "conversions": "sum"
        }
        
        # Remove None values
        agg_methods = {k: v for k, v in agg_methods.items() if v is not None and k in df.columns}
        
        # Aggregate
        df_agg = df.groupby("domain").agg(agg_methods).reset_index()
        
        # Recalculate derived metrics
        if "total_spend" in df_agg.columns and "impressions" in df_agg.columns:
            df_agg["ecpm"] = (df_agg["total_spend"] / df_agg["impressions"]) * 1000
        
        if "clicks" in df_agg.columns and "impressions" in df_agg.columns:
            df_agg["ctr"] = df_agg["clicks"] / df_agg["impressions"]
        
        if "conversions" in df_agg.columns and "impressions" in df_agg.columns:
            df_agg["conversion_rate"] = df_agg["conversions"] / df_agg["impressions"]
        
        # Handle impression-weighted averages for any remaining metrics
        impression_weighted_cols = ["completion_rate"]
        for col in impression_weighted_cols:
            if col in df.columns:
                # Calculate weighted average
                df_agg[col] = (
                    df.groupby("domain").apply(
                        lambda x: (x[col] * x["impressions"]).sum() / x["impressions"].sum()
                    ).reset_index(drop=True)
                )
        
        logger.info(f"Aggregated from {len(df)} to {len(df_agg)} domain-level rows")
        return df_agg
    
    def _apply_volume_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply minimum volume requirements"""
        initial_count = len(df)
        
        # Minimum impressions threshold (250 for whitelists/blacklists)
        min_impressions = 250
        
        # For PulsePoint, also apply 0.05% of total impressions filter
        if self.config.platform.value == "pulsepoint":
            total_impressions = df["impressions"].sum()
            min_impression_percentage = total_impressions * 0.0005  # 0.05%
            
            # Apply both filters
            df = df[
                (df["impressions"] >= min_impressions) & 
                (df["impressions"] >= min_impression_percentage)
            ]
        else:
            # For Trade Desk, just apply minimum impressions
            df = df[df["impressions"] >= min_impressions]
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            self.data_quality_issues.append(
                f"Removed {removed_count} rows below minimum volume threshold"
            )
        
        return df
    
    def _validate_data_quality(self, df: pd.DataFrame):
        """Perform final data quality validation"""
        
        # Check for negative values in metrics that shouldn't be negative
        non_negative_columns = ["impressions", "clicks", "conversions", "total_spend"]
        for col in non_negative_columns:
            if col in df.columns:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    self.data_quality_issues.append(
                        f"Found {negative_count} negative values in {col}"
                    )
        
        # Check for percentage values outside valid range
        percentage_columns = ["ctr", "conversion_rate", "completion_rate"]
        for col in percentage_columns:
            if col in df.columns:
                invalid_count = ((df[col] < 0) | (df[col] > 1)).sum()
                if invalid_count > 0:
                    self.data_quality_issues.append(
                        f"Found {invalid_count} invalid percentage values in {col}"
                    )
        
        # Check for extremely high CPM values (potential data quality issues)
        if "cpm" in df.columns:
            high_cpm_count = (df["cpm"] > 1000).sum()  # $1000+ CPM
            if high_cpm_count > 0:
                self.data_quality_issues.append(
                    f"Found {high_cpm_count} rows with extremely high CPM (>$1000)"
                )
        
        # Log quality issues
        if self.data_quality_issues:
            logger.warning(f"Data quality issues found: {self.data_quality_issues}")
        else:
            logger.info("No data quality issues detected")
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of the preprocessing results"""
        return {
            "column_mapping": self.column_mapping,
            "data_quality_issues": self.data_quality_issues,
            "config_used": {
                "platform": self.config.platform.value,
                "goal": self.config.goal.value,
                "channel": self.config.channel.value,
                "analysis_level": self.config.analysis_level
            }
        }

