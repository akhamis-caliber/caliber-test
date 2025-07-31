import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import logging

from scoring_service.config import ScoringConfig, MetricConfig

logger = logging.getLogger(__name__)

class DataNormalizer:
    """Handles normalization of metrics to 0-100 scale using min-max normalization"""
    
    def __init__(self, config: ScoringConfig):
        self.config = config
        self.normalization_stats = {}
    
    def normalize_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize all metrics to 0-100 scale
        Returns: (normalized_dataframe, normalization_statistics)
        """
        logger.info(f"Starting normalization for {len(df)} rows")
        
        df_normalized = df.copy()
        normalization_stats = {}
        
        # Normalize each metric according to configuration
        for metric in self.config.metrics:
            if metric.name in df.columns:
                df_normalized, metric_stats = self._normalize_metric(
                    df_normalized, metric.name, metric.is_higher_better
                )
                normalization_stats[metric.name] = metric_stats
            else:
                logger.warning(f"Metric {metric.name} not found in data")
        
        self.normalization_stats = normalization_stats
        
        logger.info("Normalization complete")
        return df_normalized, normalization_stats
    
    def _normalize_metric(
        self, 
        df: pd.DataFrame, 
        metric_name: str, 
        is_higher_better: bool
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """
        Normalize a single metric using min-max normalization
        """
        values = df[metric_name].copy()
        
        # Handle missing values
        valid_mask = pd.notna(values) & np.isfinite(values)
        valid_values = values[valid_mask]
        
        if len(valid_values) == 0:
            logger.warning(f"No valid values found for metric {metric_name}")
            df[f"{metric_name}_normalized"] = 0
            return df, {"min": 0, "max": 0, "count": 0}
        
        min_val = valid_values.min()
        max_val = valid_values.max()
        
        # Handle edge case where all values are the same
        if min_val == max_val:
            logger.warning(f"All values identical for metric {metric_name}: {min_val}")
            df[f"{metric_name}_normalized"] = 50  # Assign middle score
            return df, {"min": min_val, "max": max_val, "count": len(valid_values)}
        
        # Apply min-max normalization
        if is_higher_better:
            # Higher values get higher scores
            normalized = (values - min_val) / (max_val - min_val) * 100
        else:
            # Lower values get higher scores (inverse normalization)
            normalized = (max_val - values) / (max_val - min_val) * 100
        
        # Handle any remaining invalid values
        normalized = normalized.fillna(0)
        normalized = np.clip(normalized, 0, 100)
        
        df[f"{metric_name}_normalized"] = normalized
        
        stats = {
            "min": float(min_val),
            "max": float(max_val),
            "count": len(valid_values),
            "is_higher_better": is_higher_better
        }
        
        logger.debug(f"Normalized {metric_name}: min={min_val:.4f}, max={max_val:.4f}")
        return df, stats
    
    def get_normalization_report(self) -> Dict[str, Any]:
        """Get detailed normalization report"""
        return {
            "metrics_normalized": list(self.normalization_stats.keys()),
            "normalization_stats": self.normalization_stats,
            "config_used": {
                "platform": self.config.platform.value,
                "goal": self.config.goal.value,
                "channel": self.config.channel.value,
                "ctr_sensitivity": self.config.ctr_sensitivity
            }
        }

