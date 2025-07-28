import openai
from typing import List, Dict, Any
import json
from config.settings import settings

openai.api_key = settings.OPENAI_API_KEY

def generate_score_explanation(
    scoring_results: List[Any], 
    explanation_type: str = "comprehensive",
    detail_level: str = "detailed"
) -> str:
    """
    Generate AI explanation for scoring results
    
    Args:
        scoring_results: List of scoring result objects
        explanation_type: Type of explanation (comprehensive, summary, technical)
        detail_level: Level of detail (basic, detailed, expert)
        
    Returns:
        Generated explanation text
    """
    try:
        # Prepare data for explanation
        explanation_data = prepare_explanation_data(scoring_results)
        
        # Generate explanation based on type and detail level
        if explanation_type == "comprehensive":
            return generate_comprehensive_explanation(explanation_data, detail_level)
        elif explanation_type == "summary":
            return generate_summary_explanation(explanation_data, detail_level)
        elif explanation_type == "technical":
            return generate_technical_explanation(explanation_data, detail_level)
        else:
            return generate_comprehensive_explanation(explanation_data, detail_level)
            
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

def prepare_explanation_data(scoring_results: List[Any]) -> Dict[str, Any]:
    """Prepare scoring data for explanation generation"""
    data = {
        "total_metrics": len(scoring_results),
        "metrics": [],
        "final_score": 0,
        "score_breakdown": {}
    }
    
    for result in scoring_results:
        metric_data = {
            "name": result.metric_name,
            "value": result.metric_value,
            "score": result.score,
            "weight": result.weight,
            "weighted_score": result.weighted_score,
            "explanation": result.explanation
        }
        data["metrics"].append(metric_data)
        data["final_score"] += result.weighted_score or 0
        
        # Group by metric type
        if result.metric_name not in data["score_breakdown"]:
            data["score_breakdown"][result.metric_name] = []
        data["score_breakdown"][result.metric_name].append(metric_data)
    
    return data

def generate_comprehensive_explanation(data: Dict[str, Any], detail_level: str) -> str:
    """Generate comprehensive explanation of scoring results"""
    prompt = f"""
    Generate a comprehensive explanation of these scoring results:
    
    Data: {json.dumps(data, indent=2)}
    
    Detail Level: {detail_level}
    
    Please provide:
    1. Overall score interpretation
    2. Breakdown of each metric's contribution
    3. Key factors affecting the score
    4. Areas of strength and weakness
    5. Context and implications
    
    Make the explanation {detail_level} and easy to understand.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert data analyst explaining scoring results in clear, actionable terms."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating comprehensive explanation: {str(e)}"

def generate_summary_explanation(data: Dict[str, Any], detail_level: str) -> str:
    """Generate summary explanation of scoring results"""
    prompt = f"""
    Generate a concise summary of these scoring results:
    
    Data: {json.dumps(data, indent=2)}
    
    Detail Level: {detail_level}
    
    Provide a brief summary covering:
    1. Overall score
    2. Top contributing factors
    3. Main takeaway
    
    Keep it concise and {detail_level}.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a data analyst providing concise summaries of scoring results."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating summary explanation: {str(e)}"

def generate_technical_explanation(data: Dict[str, Any], detail_level: str) -> str:
    """Generate technical explanation of scoring results"""
    prompt = f"""
    Generate a technical explanation of these scoring results:
    
    Data: {json.dumps(data, indent=2)}
    
    Detail Level: {detail_level}
    
    Provide a technical analysis covering:
    1. Mathematical breakdown of scoring
    2. Weight calculations and impact
    3. Statistical significance
    4. Algorithm details
    5. Technical recommendations
    
    Make it {detail_level} and technically accurate.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a data scientist providing technical analysis of scoring algorithms and results."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.5
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating technical explanation: {str(e)}"

def generate_metric_specific_explanation(metric_data: Dict[str, Any]) -> str:
    """Generate explanation for a specific metric"""
    prompt = f"""
    Explain this specific metric result:
    
    Metric: {metric_data['name']}
    Value: {metric_data['value']}
    Score: {metric_data['score']}
    Weight: {metric_data['weight']}
    Weighted Score: {metric_data['weighted_score']}
    Explanation: {metric_data['explanation']}
    
    Provide a clear explanation of what this metric means and why it received this score.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert explaining individual metric scores in clear terms."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating metric explanation: {str(e)}" 