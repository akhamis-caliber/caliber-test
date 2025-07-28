import openai
from typing import Dict, List, Any
import pandas as pd
import json
from config.settings import settings

openai.api_key = settings.OPENAI_API_KEY

def generate_ai_insights(scores_df: pd.DataFrame, campaign_id: int) -> Dict[str, Any]:
    """
    Generate AI-powered insights from scoring results
    
    Args:
        scores_df: DataFrame with scoring results
        campaign_id: ID of the campaign
        
    Returns:
        Dictionary containing AI-generated insights
    """
    try:
        # Prepare data summary for AI analysis
        data_summary = prepare_data_summary(scores_df)
        
        # Generate insights using OpenAI
        insights = generate_openai_insights(data_summary, campaign_id)
        
        # Generate recommendations
        recommendations = generate_recommendations(scores_df, insights)
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "key_findings": extract_key_findings(scores_df),
            "trends": identify_trends(scores_df)
        }
        
    except Exception as e:
        return {
            "error": f"Failed to generate AI insights: {str(e)}",
            "insights": [],
            "recommendations": []
        }

def prepare_data_summary(scores_df: pd.DataFrame) -> Dict[str, Any]:
    """Prepare a summary of the data for AI analysis"""
    return {
        "total_records": len(scores_df),
        "score_statistics": {
            "mean": float(scores_df['final_score'].mean()),
            "median": float(scores_df['final_score'].median()),
            "std": float(scores_df['final_score'].std()),
            "min": float(scores_df['final_score'].min()),
            "max": float(scores_df['final_score'].max())
        },
        "score_distribution": {
            "excellent": int(len(scores_df[scores_df['final_score'] >= 80])),
            "good": int(len(scores_df[(scores_df['final_score'] >= 60) & (scores_df['final_score'] < 80)])),
            "average": int(len(scores_df[(scores_df['final_score'] >= 40) & (scores_df['final_score'] < 60)])),
            "below_average": int(len(scores_df[(scores_df['final_score'] >= 20) & (scores_df['final_score'] < 40)])),
            "poor": int(len(scores_df[scores_df['final_score'] < 20]))
        },
        "columns": list(scores_df.columns),
        "top_performers": scores_df.nlargest(5, 'final_score')[['final_score']].to_dict('records'),
        "bottom_performers": scores_df.nsmallest(5, 'final_score')[['final_score']].to_dict('records')
    }

def generate_openai_insights(data_summary: Dict[str, Any], campaign_id: int) -> List[str]:
    """Generate insights using OpenAI GPT"""
    prompt = f"""
    Analyze the following scoring data and provide 5-7 key insights:
    
    Data Summary:
    {json.dumps(data_summary, indent=2)}
    
    Campaign ID: {campaign_id}
    
    Please provide:
    1. Key patterns in the data
    2. Notable outliers or anomalies
    3. Performance trends
    4. Areas of concern
    5. Positive indicators
    
    Format your response as a JSON array of insight strings.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a data analyst expert. Provide clear, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse the response
        content = response.choices[0].message.content
        try:
            insights = json.loads(content)
            if isinstance(insights, list):
                return insights
            else:
                return [content]  # Fallback if JSON parsing fails
        except json.JSONDecodeError:
            return [content]  # Return raw content if JSON parsing fails
            
    except Exception as e:
        return [f"Error generating AI insights: {str(e)}"]

def generate_recommendations(scores_df: pd.DataFrame, insights: List[str]) -> List[str]:
    """Generate actionable recommendations based on insights"""
    prompt = f"""
    Based on these insights:
    {json.dumps(insights, indent=2)}
    
    And the score distribution:
    - Excellent: {len(scores_df[scores_df['final_score'] >= 80])}
    - Good: {len(scores_df[(scores_df['final_score'] >= 60) & (scores_df['final_score'] < 80)])}
    - Average: {len(scores_df[(scores_df['final_score'] >= 40) & (scores_df['final_score'] < 60)])}
    - Below Average: {len(scores_df[(scores_df['final_score'] >= 20) & (scores_df['final_score'] < 40)])}
    - Poor: {len(scores_df[scores_df['final_score'] < 20])}
    
    Provide 3-5 actionable recommendations for improvement.
    Format as a JSON array of recommendation strings.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a business consultant. Provide practical, actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        try:
            recommendations = json.loads(content)
            if isinstance(recommendations, list):
                return recommendations
            else:
                return [content]
        except json.JSONDecodeError:
            return [content]
            
    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"]

def extract_key_findings(scores_df: pd.DataFrame) -> List[str]:
    """Extract key findings from the scoring data"""
    findings = []
    
    # Score distribution analysis
    excellent_count = len(scores_df[scores_df['final_score'] >= 80])
    poor_count = len(scores_df[scores_df['final_score'] < 20])
    
    if excellent_count > 0:
        findings.append(f"{excellent_count} entities achieved excellent scores (80+)")
    
    if poor_count > 0:
        findings.append(f"{poor_count} entities need immediate attention (score < 20)")
    
    # Score range analysis
    score_range = scores_df['final_score'].max() - scores_df['final_score'].min()
    findings.append(f"Score range: {score_range:.1f} points")
    
    # Performance gaps
    if score_range > 50:
        findings.append("Significant performance gaps exist across entities")
    
    return findings

def identify_trends(scores_df: pd.DataFrame) -> Dict[str, Any]:
    """Identify trends in the scoring data"""
    trends = {
        "score_distribution": "normal" if scores_df['final_score'].skew() < 0.5 else "skewed",
        "variability": "high" if scores_df['final_score'].std() > 20 else "low",
        "performance_level": "good" if scores_df['final_score'].mean() > 60 else "needs_improvement"
    }
    
    return trends 