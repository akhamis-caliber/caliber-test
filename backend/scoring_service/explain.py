import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import json
import logging
from enum import Enum
import openai
from config.settings import settings

logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

class ExplanationType(Enum):
    """Enumeration of explanation types"""
    SCORE_BREAKDOWN = "score_breakdown"
    FACTOR_ANALYSIS = "factor_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    TREND_ANALYSIS = "trend_analysis"
    RECOMMENDATION = "recommendation"
    ANOMALY_DETECTION = "anomaly_detection"

class ScoreExplainer:
    """
    Comprehensive score explanation system with AI integration
    """
    
    def __init__(self):
        self.explanation_cache = {}
        self.explanation_history = []
        self.campaign_contexts = {}
    
    def explain_score(self, scores_df: pd.DataFrame, campaign_id: int, 
                     explanation_type: ExplanationType = ExplanationType.SCORE_BREAKDOWN,
                     target_entity: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive score explanations
        
        Args:
            scores_df: DataFrame with scoring results
            campaign_id: Campaign identifier
            explanation_type: Type of explanation to generate
            target_entity: Specific entity to explain (if applicable)
            
        Returns:
            Dictionary containing explanations and insights
        """
        try:
            # Prepare context for explanation
            context = self._prepare_explanation_context(scores_df, campaign_id, target_entity)
            
            # Generate explanation based on type
            if explanation_type == ExplanationType.SCORE_BREAKDOWN:
                explanation = self._generate_score_breakdown(context)
            elif explanation_type == ExplanationType.FACTOR_ANALYSIS:
                explanation = self._generate_factor_analysis(context)
            elif explanation_type == ExplanationType.COMPARATIVE_ANALYSIS:
                explanation = self._generate_comparative_analysis(context)
            elif explanation_type == ExplanationType.TREND_ANALYSIS:
                explanation = self._generate_trend_analysis(context)
            elif explanation_type == ExplanationType.RECOMMENDATION:
                explanation = self._generate_recommendations(context)
            elif explanation_type == ExplanationType.ANOMALY_DETECTION:
                explanation = self._generate_anomaly_analysis(context)
            else:
                explanation = self._generate_general_explanation(context)
            
            # Store explanation in history
            self.explanation_history.append({
                'campaign_id': campaign_id,
                'explanation_type': explanation_type.value,
                'target_entity': target_entity,
                'timestamp': pd.Timestamp.now(),
                'explanation': explanation
            })
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {
                'error': f"Failed to generate explanation: {str(e)}",
                'explanation_type': explanation_type.value,
                'content': []
            }
    
    def _prepare_explanation_context(self, scores_df: pd.DataFrame, campaign_id: int, 
                                   target_entity: Optional[str] = None) -> Dict[str, Any]:
        """Prepare context for explanation generation"""
        context = {
            'campaign_id': campaign_id,
            'total_entities': len(scores_df),
            'score_statistics': {
                'mean': float(scores_df['final_score'].mean()),
                'median': float(scores_df['final_score'].median()),
                'std': float(scores_df['final_score'].std()),
                'min': float(scores_df['final_score'].min()),
                'max': float(scores_df['final_score'].max())
            },
            'score_distribution': self._calculate_score_distribution(scores_df),
            'available_columns': list(scores_df.columns),
            'target_entity': target_entity
        }
        
        # Add target entity specific data if provided
        if target_entity and 'Domain' in scores_df.columns:
            entity_data = scores_df[scores_df['Domain'] == target_entity]
            if not entity_data.empty:
                context['target_entity_data'] = entity_data.iloc[0].to_dict()
                context['target_entity_rank'] = int(scores_df[scores_df['final_score'] >= entity_data.iloc[0]['final_score']].shape[0])
        
        # Add top and bottom performers
        context['top_performers'] = scores_df.nlargest(5, 'final_score')[['Domain', 'final_score']].to_dict('records') if 'Domain' in scores_df.columns else []
        context['bottom_performers'] = scores_df.nsmallest(5, 'final_score')[['Domain', 'final_score']].to_dict('records') if 'Domain' in scores_df.columns else []
        
        return context
    
    def _calculate_score_distribution(self, scores_df: pd.DataFrame) -> Dict[str, int]:
        """Calculate score distribution across categories"""
        return {
            'excellent': int(len(scores_df[scores_df['final_score'] >= 80])),
            'good': int(len(scores_df[(scores_df['final_score'] >= 60) & (scores_df['final_score'] < 80)])),
            'average': int(len(scores_df[(scores_df['final_score'] >= 40) & (scores_df['final_score'] < 60)])),
            'below_average': int(len(scores_df[(scores_df['final_score'] >= 20) & (scores_df['final_score'] < 40)])),
            'poor': int(len(scores_df[scores_df['final_score'] < 20]))
        }
    
    def _generate_score_breakdown(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed score breakdown explanation"""
        prompt = f"""
        Analyze the scoring results and provide a detailed breakdown:
        
        Campaign Context: {json.dumps(context, indent=2)}
        
        Please provide:
        1. Overall performance summary
        2. Score distribution analysis
        3. Key factors influencing scores
        4. Performance insights for different score ranges
        5. Notable patterns or trends
        
        Format as a JSON object with sections: summary, distribution_analysis, key_factors, insights, patterns
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a data analyst expert. Provide clear, detailed score breakdowns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            try:
                breakdown = json.loads(content)
                return {
                    'type': 'score_breakdown',
                    'content': breakdown,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'score_breakdown',
                    'content': {'raw_explanation': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'score_breakdown',
                'error': f"Failed to generate score breakdown: {str(e)}",
                'content': {}
            }
    
    def _generate_factor_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate factor analysis explanation"""
        prompt = f"""
        Perform a factor analysis on the scoring data:
        
        Context: {json.dumps(context, indent=2)}
        
        Analyze:
        1. Which factors contribute most to high scores
        2. Which factors are most problematic for low scores
        3. Factor correlations and interactions
        4. Factor importance ranking
        5. Factor-specific recommendations
        
        Format as JSON with sections: factor_importance, correlations, recommendations, insights
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a statistical analyst. Provide detailed factor analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.6
            )
            
            content = response.choices[0].message.content
            try:
                analysis = json.loads(content)
                return {
                    'type': 'factor_analysis',
                    'content': analysis,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'factor_analysis',
                    'content': {'raw_analysis': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'factor_analysis',
                'error': f"Failed to generate factor analysis: {str(e)}",
                'content': {}
            }
    
    def _generate_comparative_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparative analysis explanation"""
        prompt = f"""
        Provide a comparative analysis of the scoring results:
        
        Context: {json.dumps(context, indent=2)}
        
        Compare:
        1. Top performers vs bottom performers
        2. Performance gaps and their causes
        3. Benchmark comparisons
        4. Relative performance insights
        5. Competitive positioning analysis
        
        Format as JSON with sections: performance_comparison, gaps_analysis, benchmarks, insights
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a business analyst. Provide comparative insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            try:
                comparison = json.loads(content)
                return {
                    'type': 'comparative_analysis',
                    'content': comparison,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'comparative_analysis',
                    'content': {'raw_comparison': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'comparative_analysis',
                'error': f"Failed to generate comparative analysis: {str(e)}",
                'content': {}
            }
    
    def _generate_trend_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend analysis explanation"""
        prompt = f"""
        Analyze trends in the scoring data:
        
        Context: {json.dumps(context, indent=2)}
        
        Identify:
        1. Overall performance trends
        2. Score distribution trends
        3. Factor trend patterns
        4. Seasonal or cyclical patterns
        5. Trend-based predictions
        
        Format as JSON with sections: overall_trends, distribution_trends, factor_trends, predictions
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a trend analyst. Identify patterns and predict future trends."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.6
            )
            
            content = response.choices[0].message.content
            try:
                trends = json.loads(content)
                return {
                    'type': 'trend_analysis',
                    'content': trends,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'trend_analysis',
                    'content': {'raw_trends': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'trend_analysis',
                'error': f"Failed to generate trend analysis: {str(e)}",
                'content': {}
            }
    
    def _generate_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable recommendations"""
        prompt = f"""
        Generate actionable recommendations based on the scoring results:
        
        Context: {json.dumps(context, indent=2)}
        
        Provide:
        1. Immediate action items
        2. Strategic recommendations
        3. Process improvements
        4. Resource allocation suggestions
        5. Risk mitigation strategies
        
        Format as JSON with sections: immediate_actions, strategic_recommendations, process_improvements, resource_allocation, risk_mitigation
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a business consultant. Provide practical, actionable recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            try:
                recommendations = json.loads(content)
                return {
                    'type': 'recommendations',
                    'content': recommendations,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'recommendations',
                    'content': {'raw_recommendations': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'recommendations',
                'error': f"Failed to generate recommendations: {str(e)}",
                'content': {}
            }
    
    def _generate_anomaly_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate anomaly detection analysis"""
        prompt = f"""
        Analyze anomalies in the scoring data:
        
        Context: {json.dumps(context, indent=2)}
        
        Identify:
        1. Statistical anomalies
        2. Outlier patterns
        3. Unusual score distributions
        4. Data quality issues
        5. Anomaly explanations
        
        Format as JSON with sections: statistical_anomalies, outlier_patterns, distribution_issues, data_quality, explanations
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a data quality analyst. Identify and explain anomalies."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            
            content = response.choices[0].message.content
            try:
                anomalies = json.loads(content)
                return {
                    'type': 'anomaly_analysis',
                    'content': anomalies,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'anomaly_analysis',
                    'content': {'raw_anomalies': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'anomaly_analysis',
                'error': f"Failed to generate anomaly analysis: {str(e)}",
                'content': {}
            }
    
    def _generate_general_explanation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general explanation"""
        prompt = f"""
        Provide a general explanation of the scoring results:
        
        Context: {json.dumps(context, indent=2)}
        
        Explain:
        1. What the scores mean
        2. Key insights from the data
        3. Important patterns
        4. Overall assessment
        5. Next steps
        
        Format as JSON with sections: score_meaning, key_insights, patterns, assessment, next_steps
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a data analyst. Provide clear, general explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            try:
                explanation = json.loads(content)
                return {
                    'type': 'general_explanation',
                    'content': explanation,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'type': 'general_explanation',
                    'content': {'raw_explanation': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'type': 'general_explanation',
                'error': f"Failed to generate general explanation: {str(e)}",
                'content': {}
            }
    
    def explain_entity_score(self, scores_df: pd.DataFrame, entity_name: str, 
                           campaign_id: int) -> Dict[str, Any]:
        """
        Generate explanation for a specific entity's score
        
        Args:
            scores_df: DataFrame with scoring results
            entity_name: Name of the entity to explain
            campaign_id: Campaign identifier
            
        Returns:
            Entity-specific explanation
        """
        if 'Domain' not in scores_df.columns:
            return {'error': 'Domain column not found in data'}
        
        entity_data = scores_df[scores_df['Domain'] == entity_name]
        if entity_data.empty:
            return {'error': f'Entity {entity_name} not found in data'}
        
        entity_row = entity_data.iloc[0]
        entity_rank = int(scores_df[scores_df['final_score'] >= entity_row['final_score']].shape[0])
        
        prompt = f"""
        Explain the score for entity: {entity_name}
        
        Entity Data: {entity_row.to_dict()}
        Entity Rank: {entity_rank} out of {len(scores_df)}
        Campaign ID: {campaign_id}
        
        Overall Score Statistics:
        - Mean: {scores_df['final_score'].mean():.2f}
        - Median: {scores_df['final_score'].median():.2f}
        - Std: {scores_df['final_score'].std():.2f}
        
        Please explain:
        1. Why this entity received this score
        2. How it compares to others
        3. Key strengths and weaknesses
        4. Improvement opportunities
        5. Context within the campaign
        
        Format as JSON with sections: score_explanation, comparison, strengths_weaknesses, improvements, context
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a performance analyst. Explain individual entity scores clearly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            try:
                explanation = json.loads(content)
                return {
                    'entity_name': entity_name,
                    'entity_score': float(entity_row['final_score']),
                    'entity_rank': entity_rank,
                    'total_entities': len(scores_df),
                    'explanation': explanation,
                    'generated_at': pd.Timestamp.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'entity_name': entity_name,
                    'entity_score': float(entity_row['final_score']),
                    'entity_rank': entity_rank,
                    'total_entities': len(scores_df),
                    'explanation': {'raw_explanation': content},
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
        except Exception as e:
            return {
                'entity_name': entity_name,
                'error': f"Failed to explain entity score: {str(e)}",
                'explanation': {}
            }
    
    def get_explanation_history(self, campaign_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get explanation history for a campaign or all campaigns"""
        if campaign_id:
            return [exp for exp in self.explanation_history if exp['campaign_id'] == campaign_id]
        return self.explanation_history
    
    def clear_explanation_cache(self) -> None:
        """Clear the explanation cache"""
        self.explanation_cache.clear()
        logger.info("Explanation cache cleared") 