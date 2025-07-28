import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from config.settings import settings

def analyze_trends_over_time(
    scoring_history: List[Any], 
    time_period: str = "30d"
) -> Dict[str, Any]:
    """
    Analyze trends in scoring data over time
    
    Args:
        scoring_history: List of scoring history objects
        time_period: Time period for analysis (e.g., "7d", "30d", "90d")
        
    Returns:
        Dictionary containing trend analysis results
    """
    try:
        # Convert to DataFrame
        history_df = prepare_history_data(scoring_history)
        
        if history_df.empty:
            return {
                "trends": [],
                "patterns": {},
                "insights": [],
                "forecast": {},
                "summary": "No historical data available for trend analysis"
            }
        
        # Filter by time period
        filtered_df = filter_by_time_period(history_df, time_period)
        
        # Analyze trends
        trends = identify_trends(filtered_df)
        patterns = identify_patterns(filtered_df)
        insights = generate_trend_insights(filtered_df, trends, patterns)
        forecast = generate_forecast(filtered_df)
        
        return {
            "trends": trends,
            "patterns": patterns,
            "insights": insights,
            "forecast": forecast,
            "summary": generate_trend_summary(trends, patterns, insights)
        }
        
    except Exception as e:
        return {
            "error": f"Error analyzing trends: {str(e)}",
            "trends": [],
            "patterns": {},
            "insights": [],
            "forecast": {}
        }

def prepare_history_data(scoring_history: List[Any]) -> pd.DataFrame:
    """Prepare scoring history data for analysis"""
    data = []
    
    for history in scoring_history:
        if hasattr(history, 'results_summary') and history.results_summary:
            try:
                summary = json.loads(history.results_summary) if isinstance(history.results_summary, str) else history.results_summary
                
                data.append({
                    'date': history.created_at,
                    'campaign_id': history.campaign_id,
                    'version': history.version,
                    'average_score': summary.get('average_score', 0),
                    'total_records': summary.get('total_records', 0),
                    'score_distribution': summary.get('score_distribution', {}),
                    'performance_metrics': summary.get('performance_metrics', {})
                })
            except (json.JSONDecodeError, AttributeError):
                continue
    
    return pd.DataFrame(data)

def filter_by_time_period(df: pd.DataFrame, time_period: str) -> pd.DataFrame:
    """Filter data by specified time period"""
    if df.empty:
        return df
    
    # Parse time period
    period_map = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "180d": 180,
        "365d": 365
    }
    
    days = period_map.get(time_period, 30)
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Filter data
    filtered_df = df[df['date'] >= cutoff_date].copy()
    filtered_df = filtered_df.sort_values('date')
    
    return filtered_df

def identify_trends(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Identify trends in the scoring data"""
    trends = []
    
    if df.empty or len(df) < 2:
        return trends
    
    # Calculate trend for average score
    if 'average_score' in df.columns:
        score_trend = calculate_trend(df['average_score'])
        trends.append({
            "metric": "average_score",
            "trend": score_trend["direction"],
            "slope": score_trend["slope"],
            "strength": score_trend["strength"],
            "description": f"Average score is {score_trend['direction']} with {score_trend['strength']} trend"
        })
    
    # Calculate trend for total records
    if 'total_records' in df.columns:
        records_trend = calculate_trend(df['total_records'])
        trends.append({
            "metric": "total_records",
            "trend": records_trend["direction"],
            "slope": records_trend["slope"],
            "strength": records_trend["strength"],
            "description": f"Total records are {records_trend['direction']} with {records_trend['strength']} trend"
        })
    
    # Analyze score distribution trends
    if 'score_distribution' in df.columns:
        distribution_trends = analyze_distribution_trends(df)
        trends.extend(distribution_trends)
    
    return trends

def calculate_trend(series: pd.Series) -> Dict[str, Any]:
    """Calculate trend direction, slope, and strength"""
    if len(series) < 2:
        return {"direction": "stable", "slope": 0, "strength": "weak"}
    
    # Calculate linear regression
    x = np.arange(len(series))
    y = series.values
    
    # Simple linear regression
    slope = np.polyfit(x, y, 1)[0]
    
    # Determine direction
    if abs(slope) < 0.1:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"
    
    # Determine strength based on R-squared
    correlation = np.corrcoef(x, y)[0, 1]
    r_squared = correlation ** 2
    
    if r_squared > 0.7:
        strength = "strong"
    elif r_squared > 0.3:
        strength = "moderate"
    else:
        strength = "weak"
    
    return {
        "direction": direction,
        "slope": float(slope),
        "strength": strength,
        "r_squared": float(r_squared)
    }

def analyze_distribution_trends(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Analyze trends in score distribution categories"""
    trends = []
    
    # Extract distribution data
    for idx, row in df.iterrows():
        if isinstance(row['score_distribution'], dict):
            for category, count in row['score_distribution'].items():
                if category not in [col for col in df.columns if col.startswith('dist_')]:
                    df.at[idx, f'dist_{category}'] = count
    
    # Analyze trends for each distribution category
    dist_columns = [col for col in df.columns if col.startswith('dist_')]
    
    for col in dist_columns:
        if col in df.columns and not df[col].isna().all():
            trend = calculate_trend(df[col].fillna(0))
            category = col.replace('dist_', '')
            
            trends.append({
                "metric": f"distribution_{category}",
                "trend": trend["direction"],
                "slope": trend["slope"],
                "strength": trend["strength"],
                "description": f"{category} scores are {trend['direction']} with {trend['strength']} trend"
            })
    
    return trends

def identify_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Identify patterns in the scoring data"""
    patterns = {
        "seasonality": detect_seasonality(df),
        "volatility": calculate_volatility(df),
        "outliers": detect_outliers(df),
        "correlations": calculate_correlations(df)
    }
    
    return patterns

def detect_seasonality(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect seasonal patterns in the data"""
    if df.empty or len(df) < 7:
        return {"detected": False, "pattern": "insufficient_data"}
    
    # Simple seasonality detection
    if 'average_score' in df.columns:
        scores = df['average_score'].values
        
        # Check for weekly patterns
        if len(scores) >= 7:
            weekly_avg = []
            for i in range(7):
                weekly_avg.append(np.mean(scores[i::7]))
            
            weekly_variance = np.var(weekly_avg)
            if weekly_variance > np.var(scores) * 0.1:
                return {
                    "detected": True,
                    "pattern": "weekly",
                    "strength": "moderate" if weekly_variance > np.var(scores) * 0.2 else "weak"
                }
    
    return {"detected": False, "pattern": "none"}

def calculate_volatility(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate volatility in the scoring data"""
    if df.empty:
        return {"level": "unknown", "value": 0}
    
    if 'average_score' in df.columns:
        scores = df['average_score']
        volatility = scores.std() / scores.mean() if scores.mean() != 0 else 0
        
        if volatility > 0.3:
            level = "high"
        elif volatility > 0.15:
            level = "moderate"
        else:
            level = "low"
        
        return {
            "level": level,
            "value": float(volatility),
            "description": f"Score volatility is {level}"
        }
    
    return {"level": "unknown", "value": 0}

def detect_outliers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect outliers in the scoring data"""
    outliers = []
    
    if df.empty or 'average_score' not in df.columns:
        return outliers
    
    scores = df['average_score']
    
    # IQR method for outlier detection
    q1 = scores.quantile(0.25)
    q3 = scores.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outlier_indices = scores[(scores < lower_bound) | (scores > upper_bound)].index
    
    for idx in outlier_indices:
        outliers.append({
            "date": df.loc[idx, 'date'].isoformat() if pd.notna(df.loc[idx, 'date']) else None,
            "value": float(df.loc[idx, 'average_score']),
            "type": "high" if df.loc[idx, 'average_score'] > upper_bound else "low"
        })
    
    return outliers

def calculate_correlations(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate correlations between different metrics"""
    correlations = {}
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_columns) > 1:
        corr_matrix = df[numeric_columns].corr()
        
        for i, col1 in enumerate(numeric_columns):
            for col2 in numeric_columns[i+1:]:
                if pd.notna(corr_matrix.loc[col1, col2]):
                    correlations[f"{col1}_vs_{col2}"] = float(corr_matrix.loc[col1, col2])
    
    return correlations

def generate_trend_insights(df: pd.DataFrame, trends: List[Dict], patterns: Dict) -> List[str]:
    """Generate insights from trend analysis"""
    insights = []
    
    if df.empty:
        insights.append("No historical data available for trend analysis")
        return insights
    
    # Overall trend insights
    score_trends = [t for t in trends if t["metric"] == "average_score"]
    if score_trends:
        trend = score_trends[0]
        if trend["direction"] == "increasing" and trend["strength"] in ["strong", "moderate"]:
            insights.append("Scores are showing a positive upward trend, indicating improving performance")
        elif trend["direction"] == "decreasing" and trend["strength"] in ["strong", "moderate"]:
            insights.append("Scores are declining, suggesting a need for intervention")
    
    # Volatility insights
    if patterns.get("volatility", {}).get("level") == "high":
        insights.append("High score volatility indicates inconsistent performance across time periods")
    
    # Outlier insights
    outliers = patterns.get("outliers", [])
    if outliers:
        insights.append(f"Found {len(outliers)} outlier periods that may require investigation")
    
    # Seasonality insights
    seasonality = patterns.get("seasonality", {})
    if seasonality.get("detected"):
        insights.append(f"Detected {seasonality['pattern']} patterns in the data")
    
    return insights

def generate_forecast(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate simple forecast based on historical trends"""
    if df.empty or len(df) < 3 or 'average_score' not in df.columns:
        return {"available": False, "forecast": None}
    
    try:
        # Simple linear forecast
        scores = df['average_score'].values
        x = np.arange(len(scores))
        
        # Linear regression
        coeffs = np.polyfit(x, scores, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        
        # Forecast next 3 periods
        future_x = np.arange(len(scores), len(scores) + 3)
        forecast_values = slope * future_x + intercept
        
        return {
            "available": True,
            "method": "linear_regression",
            "forecast": [float(val) for val in forecast_values],
            "confidence": "medium",
            "assumptions": "Assumes current trend continues"
        }
        
    except Exception:
        return {"available": False, "forecast": None}

def generate_trend_summary(trends: List[Dict], patterns: Dict, insights: List[str]) -> str:
    """Generate a summary of trend analysis"""
    if not trends and not insights:
        return "No significant trends detected in the available data"
    
    summary_parts = []
    
    # Add key trends
    if trends:
        key_trends = [t for t in trends if t["strength"] in ["strong", "moderate"]]
        if key_trends:
            summary_parts.append(f"Key trends: {len(key_trends)} significant patterns identified")
    
    # Add volatility info
    volatility = patterns.get("volatility", {})
    if volatility.get("level") != "unknown":
        summary_parts.append(f"Volatility: {volatility['level']}")
    
    # Add outlier info
    outliers = patterns.get("outliers", [])
    if outliers:
        summary_parts.append(f"Outliers: {len(outliers)} detected")
    
    # Add insights
    if insights:
        summary_parts.append(f"Insights: {len(insights)} key findings")
    
    return ". ".join(summary_parts) if summary_parts else "Analysis complete" 