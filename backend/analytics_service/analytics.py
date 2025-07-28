import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from scipy import stats
import json

class CampaignAnalytics:
    """Enhanced analytics service for campaign performance analysis"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    def analyze_campaign_performance(self, campaign_data: pd.DataFrame, campaign_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive campaign performance analysis"""
        
        analysis = {
            "summary": self._generate_summary_stats(campaign_data),
            "trends": self._analyze_trends(campaign_data),
            "segments": self._segment_analysis(campaign_data),
            "correlations": self._correlation_analysis(campaign_data),
            "anomalies": self._detect_anomalies(campaign_data),
            "recommendations": self._generate_recommendations(campaign_data, campaign_metadata),
            "benchmarks": self._calculate_benchmarks(campaign_data),
            "forecasting": self._forecast_performance(campaign_data)
        }
        
        return analysis
    
    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive summary statistics"""
        
        summary = {
            "total_records": len(df),
            "date_range": {
                "start": df.get('date', pd.Series()).min() if 'date' in df.columns else None,
                "end": df.get('date', pd.Series()).max() if 'date' in df.columns else None
            },
            "metrics": {}
        }
        
        # Calculate metrics for numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in df.columns:
                summary["metrics"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "q25": float(df[col].quantile(0.25)),
                    "q75": float(df[col].quantile(0.75)),
                    "missing_count": int(df[col].isnull().sum()),
                    "missing_percentage": float(df[col].isnull().sum() / len(df) * 100)
                }
        
        return summary
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in the data"""
        
        trends = {
            "time_series": {},
            "growth_rates": {},
            "seasonality": {}
        }
        
        # Time series analysis if date column exists
        if 'date' in df.columns:
            df_sorted = df.sort_values('date')
            
            # Calculate growth rates for numeric columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col != 'date':
                    # Calculate period-over-period growth
                    growth_rates = df_sorted[col].pct_change().dropna()
                    trends["growth_rates"][col] = {
                        "average_growth": float(growth_rates.mean()),
                        "growth_volatility": float(growth_rates.std()),
                        "trend_direction": "increasing" if growth_rates.mean() > 0 else "decreasing"
                    }
        
        return trends
    
    def _segment_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform segmentation analysis"""
        
        segments = {
            "performance_segments": {},
            "geographic_segments": {},
            "channel_segments": {}
        }
        
        # Performance segmentation based on CTR
        if 'ctr' in df.columns:
            ctr_quantiles = df['ctr'].quantile([0.25, 0.5, 0.75])
            segments["performance_segments"]["ctr"] = {
                "low_performers": float(ctr_quantiles[0.25]),
                "medium_performers": float(ctr_quantiles[0.5]),
                "high_performers": float(ctr_quantiles[0.75]),
                "distribution": {
                    "low": int(len(df[df['ctr'] <= ctr_quantiles[0.25]])),
                    "medium": int(len(df[(df['ctr'] > ctr_quantiles[0.25]) & (df['ctr'] <= ctr_quantiles[0.75])])),
                    "high": int(len(df[df['ctr'] > ctr_quantiles[0.75]]))
                }
            }
        
        # Channel segmentation
        if 'channel' in df.columns:
            channel_stats = df.groupby('channel').agg({
                'impressions': 'sum',
                'ctr': 'mean',
                'conversions': 'sum' if 'conversions' in df.columns else lambda x: 0
            }).to_dict('index')
            segments["channel_segments"] = channel_stats
        
        return segments
    
    def _correlation_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between metrics"""
        
        correlations = {
            "correlation_matrix": {},
            "key_correlations": {},
            "insights": []
        }
        
        # Calculate correlation matrix for numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            correlations["correlation_matrix"] = corr_matrix.to_dict()
            
            # Find strong correlations
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # Strong correlation threshold
                        strong_correlations.append({
                            "variable1": corr_matrix.columns[i],
                            "variable2": corr_matrix.columns[j],
                            "correlation": float(corr_value),
                            "strength": "strong positive" if corr_value > 0 else "strong negative"
                        })
            
            correlations["key_correlations"] = strong_correlations
            
            # Generate insights
            for corr in strong_correlations:
                correlations["insights"].append(
                    f"Strong {corr['strength']} correlation between {corr['variable1']} and {corr['variable2']} (r={corr['correlation']:.3f})"
                )
        
        return correlations
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in the data"""
        
        anomalies = {
            "outliers": {},
            "unusual_patterns": [],
            "data_quality_issues": []
        }
        
        # Detect outliers using IQR method
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if len(outliers) > 0:
                anomalies["outliers"][col] = {
                    "count": int(len(outliers)),
                    "percentage": float(len(outliers) / len(df) * 100),
                    "outlier_values": outliers[col].tolist()
                }
        
        # Check for data quality issues
        for col in df.columns:
            if df[col].isnull().sum() > len(df) * 0.5:
                anomalies["data_quality_issues"].append(f"High missing values in {col}")
            
            if df[col].dtype == 'object':
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio > 0.9:
                    anomalies["data_quality_issues"].append(f"High cardinality in {col}")
        
        return anomalies
    
    def _generate_recommendations(self, df: pd.DataFrame, campaign_metadata: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Performance-based recommendations
        if 'ctr' in df.columns:
            avg_ctr = df['ctr'].mean()
            if avg_ctr < 0.01:  # 1% CTR threshold
                recommendations.append("Consider optimizing ad creative and targeting to improve CTR")
            
            ctr_std = df['ctr'].std()
            if ctr_std > avg_ctr * 0.5:
                recommendations.append("High CTR variability suggests inconsistent performance across publishers")
        
        # Budget optimization recommendations
        if 'spend' in df.columns and 'conversions' in df.columns:
            cost_per_conversion = df['spend'].sum() / df['conversions'].sum() if df['conversions'].sum() > 0 else float('inf')
            if cost_per_conversion > 100:  # High cost per conversion threshold
                recommendations.append("High cost per conversion - consider optimizing bidding strategy")
        
        # Channel-specific recommendations
        if 'channel' in df.columns:
            channel_performance = df.groupby('channel')['ctr'].mean().sort_values(ascending=False)
            best_channel = channel_performance.index[0]
            worst_channel = channel_performance.index[-1]
            
            if channel_performance.iloc[0] / channel_performance.iloc[-1] > 2:
                recommendations.append(f"Consider reallocating budget from {worst_channel} to {best_channel} based on performance")
        
        # Campaign goal-specific recommendations
        if campaign_metadata and 'goal' in campaign_metadata:
            goal = campaign_metadata['goal']
            if goal == 'awareness':
                if 'impressions' in df.columns:
                    total_impressions = df['impressions'].sum()
                    if total_impressions < 1000000:  # 1M impressions threshold
                        recommendations.append("Consider increasing budget to reach more users for awareness campaign")
            
            elif goal == 'action':
                if 'conversions' in df.columns:
                    conversion_rate = df['conversions'].sum() / df['impressions'].sum() if df['impressions'].sum() > 0 else 0
                    if conversion_rate < 0.001:  # 0.1% conversion rate threshold
                        recommendations.append("Low conversion rate - consider optimizing landing pages and user experience")
        
        return recommendations
    
    def _calculate_benchmarks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate industry benchmarks and comparisons"""
        
        benchmarks = {
            "industry_averages": {
                "ctr": 0.02,  # 2% average CTR
                "cpm": 2.50,  # $2.50 average CPM
                "conversion_rate": 0.001  # 0.1% average conversion rate
            },
            "performance_vs_benchmarks": {},
            "percentile_rankings": {}
        }
        
        # Compare against industry benchmarks
        if 'ctr' in df.columns:
            avg_ctr = df['ctr'].mean()
            benchmarks["performance_vs_benchmarks"]["ctr"] = {
                "campaign_average": float(avg_ctr),
                "industry_average": 0.02,
                "performance_ratio": float(avg_ctr / 0.02),
                "status": "above_average" if avg_ctr > 0.02 else "below_average"
            }
        
        if 'cpm' in df.columns:
            avg_cpm = df['cpm'].mean()
            benchmarks["performance_vs_benchmarks"]["cpm"] = {
                "campaign_average": float(avg_cpm),
                "industry_average": 2.50,
                "performance_ratio": float(avg_cpm / 2.50),
                "status": "below_average" if avg_cpm < 2.50 else "above_average"
            }
        
        # Calculate percentile rankings
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in df.columns:
                percentiles = df[col].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
                benchmarks["percentile_rankings"][col] = {
                    "p10": float(percentiles[0.1]),
                    "p25": float(percentiles[0.25]),
                    "p50": float(percentiles[0.5]),
                    "p75": float(percentiles[0.75]),
                    "p90": float(percentiles[0.9])
                }
        
        return benchmarks
    
    def _forecast_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Forecast future performance based on historical data"""
        
        forecasting = {
            "trend_forecast": {},
            "seasonal_patterns": {},
            "confidence_intervals": {}
        }
        
        # Simple trend forecasting using linear regression
        if 'date' in df.columns and len(df) > 10:
            df_sorted = df.sort_values('date')
            df_sorted['date_ordinal'] = pd.to_datetime(df_sorted['date']).map(datetime.toordinal)
            
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col != 'date_ordinal':
                    # Fit linear trend
                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        df_sorted['date_ordinal'], df_sorted[col]
                    )
                    
                    # Forecast next 7 days
                    last_date = df_sorted['date_ordinal'].max()
                    future_dates = range(last_date + 1, last_date + 8)
                    future_values = [intercept + slope * date for date in future_dates]
                    
                    forecasting["trend_forecast"][col] = {
                        "trend_slope": float(slope),
                        "trend_direction": "increasing" if slope > 0 else "decreasing",
                        "r_squared": float(r_value ** 2),
                        "forecast_values": [float(v) for v in future_values],
                        "confidence": "high" if r_value ** 2 > 0.7 else "medium" if r_value ** 2 > 0.3 else "low"
                    }
        
        return forecasting
    
    def generate_analytics_report(self, campaign_id: int, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive analytics report"""
        
        report = {
            "campaign_id": campaign_id,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self._generate_executive_summary(analysis_data),
            "detailed_analysis": analysis_data,
            "key_insights": self._extract_key_insights(analysis_data),
            "action_items": self._generate_action_items(analysis_data),
            "visualization_data": self._prepare_visualization_data(analysis_data)
        }
        
        return report
    
    def _generate_executive_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate executive summary of the analysis"""
        
        summary_parts = []
        
        # Performance overview
        if "summary" in analysis_data and "metrics" in analysis_data["summary"]:
            metrics = analysis_data["summary"]["metrics"]
            if "ctr" in metrics:
                avg_ctr = metrics["ctr"]["mean"]
                summary_parts.append(f"Average CTR: {avg_ctr:.3f}")
            
            if "conversions" in metrics:
                total_conversions = metrics["conversions"]["sum"] if "sum" in metrics["conversions"] else 0
                summary_parts.append(f"Total Conversions: {total_conversions}")
        
        # Key insights
        if "recommendations" in analysis_data:
            top_recommendations = analysis_data["recommendations"][:3]
            summary_parts.append(f"Top Recommendations: {', '.join(top_recommendations)}")
        
        # Performance vs benchmarks
        if "benchmarks" in analysis_data and "performance_vs_benchmarks" in analysis_data["benchmarks"]:
            benchmark_data = analysis_data["benchmarks"]["performance_vs_benchmarks"]
            if "ctr" in benchmark_data:
                status = benchmark_data["ctr"]["status"]
                summary_parts.append(f"CTR Performance: {status.replace('_', ' ').title()}")
        
        return " | ".join(summary_parts)
    
    def _extract_key_insights(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from the analysis"""
        
        insights = []
        
        # Performance insights
        if "summary" in analysis_data and "metrics" in analysis_data["summary"]:
            metrics = analysis_data["summary"]["metrics"]
            if "ctr" in metrics:
                ctr_std = metrics["ctr"]["std"]
                ctr_mean = metrics["ctr"]["mean"]
                if ctr_std > ctr_mean * 0.5:
                    insights.append("High CTR variability indicates inconsistent performance across publishers")
        
        # Correlation insights
        if "correlations" in analysis_data and "key_correlations" in analysis_data["correlations"]:
            key_correlations = analysis_data["correlations"]["key_correlations"]
            if key_correlations:
                strongest_corr = max(key_correlations, key=lambda x: abs(x["correlation"]))
                insights.append(f"Strongest correlation: {strongest_corr['variable1']} and {strongest_corr['variable2']}")
        
        # Anomaly insights
        if "anomalies" in analysis_data and "outliers" in analysis_data["anomalies"]:
            outliers = analysis_data["anomalies"]["outliers"]
            if outliers:
                most_outliers = max(outliers.items(), key=lambda x: x[1]["count"])
                insights.append(f"Most outliers found in {most_outliers[0]} column")
        
        return insights
    
    def _generate_action_items(self, analysis_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate prioritized action items"""
        
        action_items = []
        
        # High priority actions based on recommendations
        if "recommendations" in analysis_data:
            for i, rec in enumerate(analysis_data["recommendations"][:5]):
                action_items.append({
                    "priority": "high" if i < 2 else "medium",
                    "action": rec,
                    "category": "optimization"
                })
        
        # Data quality actions
        if "anomalies" in analysis_data and "data_quality_issues" in analysis_data["anomalies"]:
            for issue in analysis_data["anomalies"]["data_quality_issues"]:
                action_items.append({
                    "priority": "high",
                    "action": f"Address data quality issue: {issue}",
                    "category": "data_quality"
                })
        
        return action_items
    
    def _prepare_visualization_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for frontend visualizations"""
        
        viz_data = {
            "charts": {},
            "metrics": {},
            "tables": {}
        }
        
        # Summary metrics for dashboard
        if "summary" in analysis_data and "metrics" in analysis_data["summary"]:
            viz_data["metrics"] = analysis_data["summary"]["metrics"]
        
        # Performance segments for charts
        if "segments" in analysis_data and "performance_segments" in analysis_data["segments"]:
            viz_data["charts"]["performance_distribution"] = analysis_data["segments"]["performance_segments"]
        
        # Correlation matrix for heatmap
        if "correlations" in analysis_data and "correlation_matrix" in analysis_data["correlations"]:
            viz_data["charts"]["correlation_heatmap"] = analysis_data["correlations"]["correlation_matrix"]
        
        return viz_data 