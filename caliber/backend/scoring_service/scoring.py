import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
import logging

from scoring_service.config import ScoringConfig, MetricConfig

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Core scoring engine that applies weighted scoring based on configuration"""
    
    def __init__(self, config: ScoringConfig):
        self.config = config
        self.scoring_stats = {}
    
    def calculate_scores(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Calculate final weighted scores for all rows
        Returns: (scored_dataframe, scoring_statistics)
        """
        logger.info(f"Calculating scores for {len(df)} rows using {self.config.platform.value} config")
        
        df_scored = df.copy()
        
        # Calculate weighted score for each row
        scores = []
        score_breakdowns = []
        
        for idx, row in df.iterrows():
            score, breakdown = self._calculate_row_score(row)
            scores.append(score)
            score_breakdowns.append(breakdown)
        
        df_scored["coegi_inventory_quality_score"] = scores
        df_scored["score_breakdown"] = score_breakdowns
        
        # Calculate percentile ranks
        df_scored["percentile_rank"] = self._calculate_percentile_ranks(scores)
        
        # Assign quality status based on percentiles
        df_scored["quality_status"] = self._assign_quality_status(df_scored["percentile_rank"])
        
        # Generate scoring statistics
        scoring_stats = self._generate_scoring_stats(df_scored)
        self.scoring_stats = scoring_stats
        
        logger.info(f"Scoring complete. Average score: {np.mean(scores):.1f}")
        return df_scored, scoring_stats
    
    def _calculate_row_score(self, row: pd.Series) -> Tuple[float, Dict[str, float]]:
        """Calculate weighted score for a single row"""
        
        total_score = 0.0
        breakdown = {}
        total_weight = 0.0
        
        for metric in self.config.metrics:
            normalized_col = f"{metric.name}_normalized"
            
            if normalized_col in row and pd.notna(row[normalized_col]):
                metric_score = row[normalized_col] * metric.weight
                total_score += metric_score
                total_weight += metric.weight
                
                breakdown[metric.name] = {
                    "normalized_value": float(row[normalized_col]),
                    "weight": metric.weight,
                    "weighted_score": float(metric_score)
                }
            else:
                logger.warning(f"Missing normalized value for {metric.name}")
                breakdown[metric.name] = {
                    "normalized_value": 0.0,
                    "weight": metric.weight,
                    "weighted_score": 0.0
                }
        
        # Normalize by total weight in case of missing metrics
        if total_weight > 0:
            final_score = total_score / total_weight * 100
        else:
            final_score = 0.0
        
        # Ensure score is between 0 and 100
        final_score = np.clip(final_score, 0, 100)
        
        return round(final_score, 1), breakdown
    
    def _calculate_percentile_ranks(self, scores: List[float]) -> List[int]:
        """Calculate percentile rank for each score"""
        from scipy import stats
        
        try:
            percentiles = stats.rankdata(scores, method='average') / len(scores) * 100
            return [int(round(p)) for p in percentiles]
        except ImportError:
            # Fallback implementation without scipy
            sorted_scores = sorted(scores)
            percentiles = []
            
            for score in scores:
                rank = sum(1 for s in sorted_scores if s <= score)
                percentile = (rank / len(sorted_scores)) * 100
                percentiles.append(int(round(percentile)))
            
            return percentiles
    
    def _assign_quality_status(self, percentile_ranks: List[int]) -> List[str]:
        """Assign quality status based on percentile ranks"""
        statuses = []
        
        for percentile in percentile_ranks:
            if percentile >= 75:
                statuses.append("good")
            elif percentile >= 25:
                statuses.append("moderate")
            else:
                statuses.append("poor")
        
        return statuses
    
    def _generate_scoring_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive scoring statistics"""
        scores = df["coegi_inventory_quality_score"]
        
        stats = {
            "total_rows_scored": len(df),
            "score_distribution": {
                "mean": float(scores.mean()),
                "median": float(scores.median()),
                "std": float(scores.std()),
                "min": float(scores.min()),
                "max": float(scores.max()),
                "q25": float(scores.quantile(0.25)),
                "q75": float(scores.quantile(0.75))
            },
            "quality_distribution": df["quality_status"].value_counts().to_dict(),
            "metric_weights_used": {
                metric.name: metric.weight for metric in self.config.metrics
            },
            "scoring_config": {
                "platform": self.config.platform.value,
                "goal": self.config.goal.value,
                "channel": self.config.channel.value,
                "ctr_sensitivity": self.config.ctr_sensitivity,
                "analysis_level": self.config.analysis_level
            }
        }
        
        return stats
    
    def generate_whitelist(self, df: pd.DataFrame, min_impressions: int = 250) -> pd.DataFrame:
        """Generate whitelist (top 25% performers)"""
        
        # Filter by minimum impressions
        filtered_df = df[df["impressions"] >= min_impressions].copy()
        
        # Get top 25% by score
        score_threshold = filtered_df["coegi_inventory_quality_score"].quantile(0.75)
        whitelist_df = filtered_df[
            filtered_df["coegi_inventory_quality_score"] >= score_threshold
        ].copy()
        
        # Sort by score descending
        whitelist_df = whitelist_df.sort_values(
            "coegi_inventory_quality_score", ascending=False
        ).reset_index(drop=True)
        
        logger.info(f"Generated whitelist with {len(whitelist_df)} entries")
        return whitelist_df
    
    def generate_blacklist(self, df: pd.DataFrame, min_impressions: int = 250) -> pd.DataFrame:
        """Generate blacklist (bottom 25% performers)"""
        
        # Filter by minimum impressions
        filtered_df = df[df["impressions"] >= min_impressions].copy()
        
        # Get bottom 25% by score
        score_threshold = filtered_df["coegi_inventory_quality_score"].quantile(0.25)
        blacklist_df = filtered_df[
            filtered_df["coegi_inventory_quality_score"] <= score_threshold
        ].copy()
        
        # Sort by score ascending (worst first)
        blacklist_df = blacklist_df.sort_values(
            "coegi_inventory_quality_score", ascending=True
        ).reset_index(drop=True)
        
        logger.info(f"Generated blacklist with {len(blacklist_df)} entries")
        return blacklist_df
    
    def get_campaign_level_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate campaign-level aggregated score"""
        
        # Weighted average score by impressions
        total_impressions = df["impressions"].sum()
        if total_impressions > 0:
            weighted_score = (
                df["coegi_inventory_quality_score"] * df["impressions"]
            ).sum() / total_impressions
        else:
            weighted_score = 0.0
        
        # Additional campaign metrics
        campaign_metrics = {
            "campaign_level_score": round(weighted_score, 1),
            "total_impressions": int(total_impressions),
            "total_spend": float(df["total_spend"].sum() if "total_spend" in df.columns 
                                else df["advertiser_cost"].sum() if "advertiser_cost" in df.columns else 0),
            "average_cpm": float((df["total_spend"] if "total_spend" in df.columns 
                                else df["advertiser_cost"]).sum() / total_impressions * 1000),
            "domains_analyzed": len(df),
            "top_performing_domains": df.nlargest(5, "coegi_inventory_quality_score")[
                ["domain" if "domain" in df.columns else "supply_vendor", "coegi_inventory_quality_score"]
            ].to_dict("records"),
            "bottom_performing_domains": df.nsmallest(5, "coegi_inventory_quality_score")[
                ["domain" if "domain" in df.columns else "supply_vendor", "coegi_inventory_quality_score"]
            ].to_dict("records")
        }
        
        return campaign_metrics

class OutlierDetector:
    """Detects and flags outliers in the data"""
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
        """Detect outliers using IQR method"""
        
        df_with_outliers = df.copy()
        outlier_flags = []
        
        for idx, row in df.iterrows():
            row_outliers = []
            
            for metric in metrics:
                if metric in df.columns:
                    Q1 = df[metric].quantile(0.25)
                    Q3 = df[metric].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    if row[metric] < lower_bound or row[metric] > upper_bound:
                        row_outliers.append(f"{metric}_outlier")
            
            outlier_flags.append(row_outliers)
        
        df_with_outliers["outlier_flags"] = outlier_flags
        df_with_outliers["is_outlier"] = [len(flags) > 0 for flags in outlier_flags]
        
        return df_with_outliers

