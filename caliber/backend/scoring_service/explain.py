import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import shap

from scoring_service.config import ScoringConfigManager
from common.exceptions import ValidationError

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    """Engine for explaining scoring results and providing insights"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.explainer = None
    
    def explain_score(
        self,
        data: pd.DataFrame,
        scores: pd.Series,
        feature_columns: List[str],
        method: str = "shap"
    ) -> Dict[str, Any]:
        """Explain the scoring results using various methods"""
        
        try:
            if method == "shap":
                return self._explain_with_shap(data, scores, feature_columns)
            elif method == "feature_importance":
                return self._explain_with_feature_importance(data, scores, feature_columns)
            elif method == "correlation":
                return self._explain_with_correlation(data, scores, feature_columns)
            else:
                raise ValidationError(f"Unknown explanation method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to explain scores: {e}")
            raise ValidationError(f"Explanation failed: {str(e)}")
    
    def explain_domain_score(
        self,
        domain_data: pd.DataFrame,
        domain_score: float,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """Explain the score for a specific domain"""
        
        try:
            # Get feature values for the domain
            domain_features = domain_data[feature_columns].iloc[0]
            
            # Calculate feature contributions
            contributions = self._calculate_feature_contributions(
                domain_features, feature_columns
            )
            
            # Identify top contributing factors
            top_factors = self._get_top_contributing_factors(contributions)
            
            # Generate explanation text
            explanation = self._generate_domain_explanation(
                domain_score, contributions, top_factors
            )
            
            return {
                "domain_score": domain_score,
                "feature_contributions": contributions,
                "top_factors": top_factors,
                "explanation": explanation,
                "confidence": self._calculate_explanation_confidence(contributions)
            }
            
        except Exception as e:
            logger.error(f"Failed to explain domain score: {e}")
            raise ValidationError(f"Domain explanation failed: {str(e)}")
    
    def explain_score_changes(
        self,
        before_data: pd.DataFrame,
        after_data: pd.DataFrame,
        before_scores: pd.Series,
        after_scores: pd.Series,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """Explain changes in scores between two time periods"""
        
        try:
            # Calculate score changes
            score_changes = after_scores - before_scores
            
            # Calculate feature changes
            feature_changes = self._calculate_feature_changes(
                before_data, after_data, feature_columns
            )
            
            # Identify drivers of change
            change_drivers = self._identify_change_drivers(
                score_changes, feature_changes, feature_columns
            )
            
            # Generate change explanation
            explanation = self._generate_change_explanation(
                score_changes, change_drivers
            )
            
            return {
                "score_changes": score_changes.to_dict(),
                "feature_changes": feature_changes.to_dict(),
                "change_drivers": change_drivers,
                "explanation": explanation,
                "summary": self._generate_change_summary(score_changes, change_drivers)
            }
            
        except Exception as e:
            logger.error(f"Failed to explain score changes: {e}")
            raise ValidationError(f"Change explanation failed: {str(e)}")
    
    def _explain_with_shap(
        self,
        data: pd.DataFrame,
        scores: pd.Series,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """Explain scores using SHAP values"""
        
        # Prepare data
        X = data[feature_columns].fillna(0)
        
        # Train a simple model for SHAP
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, scores)
        
        # Create SHAP explainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        
        # Calculate feature importance
        feature_importance = np.abs(shap_values).mean(0)
        
        # Get top features
        top_features = self._get_top_features(feature_importance, feature_columns)
        
        return {
            "method": "shap",
            "feature_importance": dict(zip(feature_columns, feature_importance)),
            "top_features": top_features,
            "shap_values": shap_values.tolist(),
            "explanation": self._generate_shap_explanation(top_features)
        }
    
    def _explain_with_feature_importance(
        self,
        data: pd.DataFrame,
        scores: pd.Series,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """Explain scores using feature importance"""
        
        # Train model
        X = data[feature_columns].fillna(0)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, scores)
        
        # Get feature importance
        importance = model.feature_importances_
        top_features = self._get_top_features(importance, feature_columns)
        
        return {
            "method": "feature_importance",
            "feature_importance": dict(zip(feature_columns, importance)),
            "top_features": top_features,
            "explanation": self._generate_importance_explanation(top_features)
        }
    
    def _explain_with_correlation(
        self,
        data: pd.DataFrame,
        scores: pd.Series,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """Explain scores using correlation analysis"""
        
        # Calculate correlations
        correlations = {}
        for feature in feature_columns:
            if feature in data.columns:
                corr = data[feature].corr(scores)
                correlations[feature] = corr if not pd.isna(corr) else 0
        
        # Sort by absolute correlation
        sorted_correlations = sorted(
            correlations.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        top_features = sorted_correlations[:10]
        
        return {
            "method": "correlation",
            "correlations": correlations,
            "top_features": top_features,
            "explanation": self._generate_correlation_explanation(top_features)
        }
    
    def _calculate_feature_contributions(
        self,
        features: pd.Series,
        feature_columns: List[str]
    ) -> Dict[str, float]:
        """Calculate individual feature contributions to score"""
        
        contributions = {}
        for feature in feature_columns:
            if feature in features.index:
                # Simple contribution calculation (can be enhanced)
                value = features[feature]
                if pd.isna(value):
                    contributions[feature] = 0
                else:
                    # Normalize value and calculate contribution
                    contributions[feature] = float(value)
        
        return contributions
    
    def _get_top_contributing_factors(
        self,
        contributions: Dict[str, float],
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Get top contributing factors"""
        
        sorted_contributions = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return sorted_contributions[:top_n]
    
    def _generate_domain_explanation(
        self,
        score: float,
        contributions: Dict[str, float],
        top_factors: List[Tuple[str, float]]
    ) -> str:
        """Generate explanation text for domain score"""
        
        explanation = f"This domain received a score of {score:.2f}. "
        
        if top_factors:
            explanation += "The main factors contributing to this score are: "
            factors_text = []
            for factor, value in top_factors:
                factors_text.append(f"{factor} ({value:.2f})")
            explanation += ", ".join(factors_text) + ". "
        
        if score >= 80:
            explanation += "This is a high-performing domain with strong metrics."
        elif score >= 60:
            explanation += "This domain shows moderate performance with room for improvement."
        else:
            explanation += "This domain has low performance and may need optimization."
        
        return explanation
    
    def _calculate_explanation_confidence(
        self,
        contributions: Dict[str, float]
    ) -> float:
        """Calculate confidence in the explanation"""
        
        # Simple confidence calculation based on contribution distribution
        total_contribution = sum(abs(v) for v in contributions.values())
        if total_contribution == 0:
            return 0.0
        
        # Higher confidence if contributions are more evenly distributed
        max_contribution = max(abs(v) for v in contributions.values())
        confidence = 1 - (max_contribution / total_contribution)
        
        return min(confidence, 1.0)
    
    def _calculate_feature_changes(
        self,
        before_data: pd.DataFrame,
        after_data: pd.DataFrame,
        feature_columns: List[str]
    ) -> pd.Series:
        """Calculate changes in feature values"""
        
        changes = {}
        for feature in feature_columns:
            if feature in before_data.columns and feature in after_data.columns:
                before_mean = before_data[feature].mean()
                after_mean = after_data[feature].mean()
                changes[feature] = after_mean - before_mean
        
        return pd.Series(changes)
    
    def _identify_change_drivers(
        self,
        score_changes: pd.Series,
        feature_changes: pd.Series,
        feature_columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Identify drivers of score changes"""
        
        drivers = []
        for feature in feature_columns:
            if feature in feature_changes.index:
                feature_change = feature_changes[feature]
                # Calculate correlation between feature change and score change
                correlation = feature_changes[feature] * score_changes.mean()
                
                drivers.append({
                    "feature": feature,
                    "change": feature_change,
                    "impact": correlation,
                    "direction": "positive" if correlation > 0 else "negative"
                })
        
        # Sort by impact
        drivers.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return drivers[:10]
    
    def _generate_change_explanation(
        self,
        score_changes: pd.Series,
        change_drivers: List[Dict[str, Any]]
    ) -> str:
        """Generate explanation for score changes"""
        
        avg_change = score_changes.mean()
        
        explanation = f"Overall, scores changed by {avg_change:.2f} points. "
        
        if change_drivers:
            explanation += "The main drivers of this change were: "
            driver_texts = []
            for driver in change_drivers[:3]:
                direction = "increased" if driver["direction"] == "positive" else "decreased"
                driver_texts.append(f"{driver['feature']} {direction}")
            explanation += ", ".join(driver_texts) + ". "
        
        return explanation
    
    def _generate_change_summary(
        self,
        score_changes: pd.Series,
        change_drivers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of changes"""
        
        return {
            "average_change": score_changes.mean(),
            "change_std": score_changes.std(),
            "improved_count": (score_changes > 0).sum(),
            "declined_count": (score_changes < 0).sum(),
            "top_drivers": change_drivers[:5]
        }
    
    def _get_top_features(
        self,
        importance: np.ndarray,
        feature_names: List[str],
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """Get top features by importance"""
        
        feature_importance = list(zip(feature_names, importance))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        return feature_importance[:top_n]
    
    def _generate_shap_explanation(self, top_features: List[Tuple[str, float]]) -> str:
        """Generate explanation for SHAP analysis"""
        
        explanation = "SHAP analysis shows the following features have the strongest impact on scores: "
        feature_texts = [f"{feature} ({importance:.3f})" for feature, importance in top_features[:5]]
        explanation += ", ".join(feature_texts) + "."
        
        return explanation
    
    def _generate_importance_explanation(self, top_features: List[Tuple[str, float]]) -> str:
        """Generate explanation for feature importance analysis"""
        
        explanation = "Feature importance analysis reveals the key factors affecting scores: "
        feature_texts = [f"{feature} ({importance:.3f})" for feature, importance in top_features[:5]]
        explanation += ", ".join(feature_texts) + "."
        
        return explanation
    
    def _generate_correlation_explanation(self, top_features: List[Tuple[str, float]]) -> str:
        """Generate explanation for correlation analysis"""
        
        explanation = "Correlation analysis shows the strongest relationships with scores: "
        feature_texts = []
        for feature, correlation in top_features[:5]:
            direction = "positive" if correlation > 0 else "negative"
            feature_texts.append(f"{feature} ({direction}, {abs(correlation):.3f})")
        explanation += ", ".join(feature_texts) + "."
        
        return explanation

