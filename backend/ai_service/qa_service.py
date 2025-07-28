import openai
import pandas as pd
from typing import Dict, Any, Optional
import json
from config.settings import settings

openai.api_key = settings.OPENAI_API_KEY

def answer_question_about_data(
    scores_df: pd.DataFrame, 
    question: str, 
    campaign_id: Optional[int] = None
) -> str:
    """
    Answer questions about scoring data using AI
    
    Args:
        scores_df: DataFrame with scoring results
        question: User's question about the data
        campaign_id: Optional campaign ID for context
        
    Returns:
        AI-generated answer to the question
    """
    try:
        # Prepare data context for the AI
        data_context = prepare_data_context(scores_df, campaign_id)
        
        # Generate answer using OpenAI
        answer = generate_ai_answer(question, data_context, campaign_id)
        
        return answer
        
    except Exception as e:
        return f"Error answering question: {str(e)}"

def prepare_data_context(scores_df: pd.DataFrame, campaign_id: Optional[int] = None) -> Dict[str, Any]:
    """Prepare data context for AI analysis"""
    context = {
        "total_records": len(scores_df),
        "unique_reports": scores_df['report_id'].nunique(),
        "unique_metrics": scores_df['metric_name'].nunique(),
        "campaign_id": campaign_id,
        "score_statistics": {
            "mean_score": float(scores_df['score'].mean()),
            "median_score": float(scores_df['score'].median()),
            "std_score": float(scores_df['score'].std()),
            "min_score": float(scores_df['score'].min()),
            "max_score": float(scores_df['score'].max())
        },
        "weighted_score_statistics": {
            "mean_weighted": float(scores_df['weighted_score'].mean()),
            "median_weighted": float(scores_df['weighted_score'].median()),
            "std_weighted": float(scores_df['weighted_score'].std()),
            "min_weighted": float(scores_df['weighted_score'].min()),
            "max_weighted": float(scores_df['weighted_score'].max())
        },
        "metric_summary": {},
        "top_performers": [],
        "bottom_performers": []
    }
    
    # Calculate final scores per report
    final_scores = scores_df.groupby('report_id')['weighted_score'].sum().reset_index()
    final_scores.columns = ['report_id', 'final_score']
    
    context["final_score_statistics"] = {
        "mean_final": float(final_scores['final_score'].mean()),
        "median_final": float(final_scores['final_score'].median()),
        "std_final": float(final_scores['final_score'].std()),
        "min_final": float(final_scores['final_score'].min()),
        "max_final": float(final_scores['final_score'].max())
    }
    
    # Top and bottom performers
    context["top_performers"] = final_scores.nlargest(5, 'final_score').to_dict('records')
    context["bottom_performers"] = final_scores.nsmallest(5, 'final_score').to_dict('records')
    
    # Metric summary
    for metric in scores_df['metric_name'].unique():
        metric_data = scores_df[scores_df['metric_name'] == metric]
        context["metric_summary"][metric] = {
            "count": len(metric_data),
            "mean_score": float(metric_data['score'].mean()),
            "mean_weight": float(metric_data['weight'].mean()),
            "mean_weighted_score": float(metric_data['weighted_score'].mean())
        }
    
    return context

def generate_ai_answer(question: str, data_context: Dict[str, Any], campaign_id: Optional[int] = None) -> str:
    """Generate AI answer to user question"""
    prompt = f"""
    Answer the following question about scoring data:
    
    Question: {question}
    
    Campaign ID: {campaign_id or 'All campaigns'}
    
    Data Context:
    {json.dumps(data_context, indent=2)}
    
    Please provide a clear, accurate answer based on the data. If the question cannot be answered with the available data, explain what information is missing.
    
    Focus on:
    1. Providing specific numbers and statistics when relevant
    2. Explaining trends and patterns
    3. Giving actionable insights
    4. Being concise but comprehensive
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a data analyst expert answering questions about scoring data. Provide accurate, helpful responses based on the data provided."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def get_suggested_questions() -> list:
    """Get list of suggested questions users can ask"""
    return [
        "What is the average score across all reports?",
        "Which metrics have the highest impact on final scores?",
        "What are the top 3 performing reports?",
        "How many reports scored above 80?",
        "What is the score distribution across different performance levels?",
        "Which metrics show the most variability?",
        "What is the correlation between different metrics?",
        "How do scores compare between different campaigns?",
        "What are the common factors in high-scoring reports?",
        "Which reports need immediate attention?"
    ]

def analyze_data_patterns(scores_df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze patterns in the scoring data for Q&A context"""
    patterns = {
        "score_distribution": "normal" if scores_df['score'].skew() < 0.5 else "skewed",
        "performance_gaps": "high" if scores_df['score'].std() > 20 else "low",
        "metric_correlation": {},
        "outliers": [],
        "trends": {}
    }
    
    # Calculate final scores
    final_scores = scores_df.groupby('report_id')['weighted_score'].sum()
    
    # Identify outliers
    q1 = final_scores.quantile(0.25)
    q3 = final_scores.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = final_scores[(final_scores < lower_bound) | (final_scores > upper_bound)]
    patterns["outliers"] = outliers.index.tolist()
    
    # Metric correlations
    pivot_data = scores_df.pivot_table(
        index='report_id', 
        columns='metric_name', 
        values='score', 
        aggfunc='mean'
    )
    
    if len(pivot_data.columns) > 1:
        correlation_matrix = pivot_data.corr()
        patterns["metric_correlation"] = correlation_matrix.to_dict()
    
    return patterns

def generate_follow_up_questions(question: str, answer: str, data_context: Dict[str, Any]) -> list:
    """Generate follow-up questions based on the original question and answer"""
    prompt = f"""
    Based on this question and answer, suggest 3-5 relevant follow-up questions:
    
    Original Question: {question}
    Answer: {answer}
    
    Data Context Summary:
    - Total records: {data_context['total_records']}
    - Average final score: {data_context['final_score_statistics']['mean_final']:.2f}
    - Score range: {data_context['final_score_statistics']['max_final'] - data_context['final_score_statistics']['min_final']:.2f}
    
    Generate follow-up questions that would provide additional insights or clarification.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert data analyst suggesting relevant follow-up questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.8
        )
        
        # Parse the response to extract questions
        content = response.choices[0].message.content
        # Simple parsing - split by newlines and clean up
        questions = [q.strip().strip('1234567890.- ') for q in content.split('\n') if q.strip()]
        return questions[:5]  # Return up to 5 questions
        
    except Exception as e:
        return [
            "What factors contribute most to high scores?",
            "How do scores vary across different metrics?",
            "What are the trends in scoring over time?"
        ] 