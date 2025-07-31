import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from sklearn.feature_selection import mutual_info_regression, f_regression
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings

from scoring_service.config import ScoringConfigManager
from common.exceptions import ValidationError

logger = logging.getLogger(__name__)

class WeightingEngine:
    """Engine for calculating and applying feature weights in scoring algorithms"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_weights = {}
        self.weight_methods = {
            "equal": self._equal_weights,
            "correlation": self._correlation_weights,
            "mutual_info": self._mutual_info_weights,
            "f_score": self._f_score_weights,
            "variance": self._variance_weights,
            "custom": self._custom_weights
        }
    
    def calculate_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        method: str = "correlation",
        feature_columns: Optional[List[str]] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculate feature weights using various methods"""
        
        try:
            if feature_columns is None:
                feature_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            
            if method not in self.weight_methods:
                raise ValidationError(f"Unknown weighting method: {method}")
            
            # Calculate weights
            weights = self.weight_methods[method](
                data, target, feature_columns, custom_weights
            )
            
            # Normalize weights
            normalized_weights = self._normalize_weights(weights)
            
            # Store weights
            self.feature_weights = normalized_weights
            
            return {
                "method": method,
                "weights": normalized_weights,
                "raw_weights": weights,
                "feature_importance": self._calculate_feature_importance(normalized_weights),
                "summary": self._generate_weight_summary(normalized_weights)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate weights: {e}")
            raise ValidationError(f"Weight calculation failed: {str(e)}")
    
    def apply_weights(
        self,
        data: pd.DataFrame,
        weights: Optional[Dict[str, float]] = None,
        feature_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Apply weights to the data"""
        
        try:
            if weights is None:
                weights = self.feature_weights
            
            if feature_columns is None:
                feature_columns = list(weights.keys())
            
            weighted_data = data.copy()
            
            for column in feature_columns:
                if column in data.columns and column in weights:
                    weight = weights[column]
                    weighted_data[column] = data[column] * weight
            
            return weighted_data
            
        except Exception as e:
            logger.error(f"Failed to apply weights: {e}")
            raise ValidationError(f"Weight application failed: {str(e)}")
    
    def get_weighted_score(
        self,
        data: pd.DataFrame,
        weights: Optional[Dict[str, float]] = None,
        feature_columns: Optional[List[str]] = None
    ) -> pd.Series:
        """Calculate weighted score for each row"""
        
        try:
            if weights is None:
                weights = self.feature_weights
            
            if feature_columns is None:
                feature_columns = list(weights.keys())
            
            # Apply weights and sum
            weighted_sum = pd.Series(0.0, index=data.index)
            
            for column in feature_columns:
                if column in data.columns and column in weights:
                    weight = weights[column]
                    weighted_sum += data[column] * weight
            
            return weighted_sum
            
        except Exception as e:
            logger.error(f"Failed to calculate weighted score: {e}")
            raise ValidationError(f"Weighted score calculation failed: {str(e)}")
    
    def optimize_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        method: str = "grid_search",
        feature_columns: Optional[List[str]] = None,
        cv_folds: int = 5
    ) -> Dict[str, Any]:
        """Optimize feature weights using various methods"""
        
        try:
            if feature_columns is None:
                feature_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            
            if method == "grid_search":
                return self._optimize_with_grid_search(data, target, feature_columns, cv_folds)
            elif method == "genetic":
                return self._optimize_with_genetic(data, target, feature_columns, cv_folds)
            elif method == "bayesian":
                return self._optimize_with_bayesian(data, target, feature_columns, cv_folds)
            else:
                raise ValidationError(f"Unknown optimization method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to optimize weights: {e}")
            raise ValidationError(f"Weight optimization failed: {str(e)}")
    
    def _equal_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate equal weights for all features"""
        
        n_features = len(feature_columns)
        weight = 1.0 / n_features
        
        return {feature: weight for feature in feature_columns}
    
    def _correlation_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate weights based on correlation with target"""
        
        weights = {}
        
        for feature in feature_columns:
            if feature in data.columns:
                correlation = abs(data[feature].corr(target))
                weights[feature] = correlation if not pd.isna(correlation) else 0
        
        return weights
    
    def _mutual_info_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate weights based on mutual information"""
        
        X = data[feature_columns].fillna(data[feature_columns].median())
        
        # Calculate mutual information
        mi_scores = mutual_info_regression(X, target, random_state=42)
        
        return dict(zip(feature_columns, mi_scores))
    
    def _f_score_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate weights based on F-scores"""
        
        X = data[feature_columns].fillna(data[feature_columns].median())
        
        # Calculate F-scores
        f_scores, _ = f_regression(X, target)
        
        return dict(zip(feature_columns, f_scores))
    
    def _variance_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate weights based on feature variance"""
        
        weights = {}
        
        for feature in feature_columns:
            if feature in data.columns:
                variance = data[feature].var()
                weights[feature] = variance if not pd.isna(variance) else 0
        
        return weights
    
    def _custom_weights(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Use custom weights provided by user"""
        
        if custom_weights is None:
            raise ValidationError("Custom weights must be provided for custom weighting method")
        
        # Validate that all features have weights
        missing_features = set(feature_columns) - set(custom_weights.keys())
        if missing_features:
            raise ValidationError(f"Missing weights for features: {missing_features}")
        
        return custom_weights
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1"""
        
        total_weight = sum(abs(w) for w in weights.values())
        
        if total_weight == 0:
            # If all weights are zero, use equal weights
            n_features = len(weights)
            return {feature: 1.0 / n_features for feature in weights.keys()}
        
        return {feature: abs(weight) / total_weight for feature, weight in weights.items()}
    
    def _calculate_feature_importance(
        self,
        weights: Dict[str, float]
    ) -> List[Tuple[str, float]]:
        """Calculate feature importance ranking"""
        
        importance = [(feature, weight) for feature, weight in weights.items()]
        importance.sort(key=lambda x: x[1], reverse=True)
        
        return importance
    
    def _generate_weight_summary(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """Generate summary of weight distribution"""
        
        weight_values = list(weights.values())
        
        return {
            "total_features": len(weights),
            "weight_sum": sum(weight_values),
            "weight_mean": np.mean(weight_values),
            "weight_std": np.std(weight_values),
            "weight_min": min(weight_values),
            "weight_max": max(weight_values),
            "top_features": self._calculate_feature_importance(weights)[:5]
        }
    
    def _optimize_with_grid_search(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        cv_folds: int
    ) -> Dict[str, Any]:
        """Optimize weights using grid search"""
        
        # Simple grid search implementation
        best_score = -np.inf
        best_weights = None
        
        # Generate weight combinations
        weight_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        for i in range(len(weight_values)):
            for j in range(len(weight_values)):
                if i + j < len(feature_columns):
                    weights = {}
                    weights[feature_columns[0]] = weight_values[i]
                    weights[feature_columns[1]] = weight_values[j]
                    
                    # Equal weights for remaining features
                    remaining_weight = 1.0 - weight_values[i] - weight_values[j]
                    remaining_features = feature_columns[2:]
                    if remaining_features:
                        equal_weight = remaining_weight / len(remaining_features)
                        for feature in remaining_features:
                            weights[feature] = equal_weight
                    
                    # Calculate score (simple correlation)
                    weighted_data = self.apply_weights(data, weights, feature_columns)
                    weighted_score = self.get_weighted_score(weighted_data, weights, feature_columns)
                    score = abs(weighted_score.corr(target))
                    
                    if score > best_score:
                        best_score = score
                        best_weights = weights
        
        return {
            "method": "grid_search",
            "best_weights": best_weights,
            "best_score": best_score,
            "optimization_history": []
        }
    
    def _optimize_with_genetic(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        cv_folds: int
    ) -> Dict[str, Any]:
        """Optimize weights using genetic algorithm (simplified)"""
        
        # Simplified genetic algorithm implementation
        population_size = 20
        generations = 10
        
        # Initialize population
        population = []
        for _ in range(population_size):
            weights = {}
            remaining_weight = 1.0
            for i, feature in enumerate(feature_columns):
                if i == len(feature_columns) - 1:
                    weights[feature] = remaining_weight
                else:
                    weight = np.random.uniform(0, remaining_weight)
                    weights[feature] = weight
                    remaining_weight -= weight
            population.append(weights)
        
        best_weights = None
        best_score = -np.inf
        history = []
        
        for generation in range(generations):
            # Evaluate population
            scores = []
            for weights in population:
                weighted_data = self.apply_weights(data, weights, feature_columns)
                weighted_score = self.get_weighted_score(weighted_data, weights, feature_columns)
                score = abs(weighted_score.corr(target))
                scores.append(score)
                
                if score > best_score:
                    best_score = score
                    best_weights = weights.copy()
            
            history.append({
                "generation": generation,
                "best_score": max(scores),
                "avg_score": np.mean(scores)
            })
            
            # Selection and crossover (simplified)
            new_population = []
            for _ in range(population_size):
                # Tournament selection
                idx1, idx2 = np.random.choice(len(population), 2, replace=False)
                parent1 = population[idx1] if scores[idx1] > scores[idx2] else population[idx2]
                parent2 = population[np.random.choice(len(population))]
                
                # Crossover
                child = {}
                for feature in feature_columns:
                    if np.random.random() < 0.5:
                        child[feature] = parent1[feature]
                    else:
                        child[feature] = parent2[feature]
                
                # Mutation
                if np.random.random() < 0.1:
                    feature = np.random.choice(feature_columns)
                    child[feature] = np.random.uniform(0, 1)
                
                # Normalize
                total_weight = sum(child.values())
                if total_weight > 0:
                    child = {k: v / total_weight for k, v in child.items()}
                
                new_population.append(child)
            
            population = new_population
        
        return {
            "method": "genetic",
            "best_weights": best_weights,
            "best_score": best_score,
            "optimization_history": history
        }
    
    def _optimize_with_bayesian(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        feature_columns: List[str],
        cv_folds: int
    ) -> Dict[str, Any]:
        """Optimize weights using Bayesian optimization (simplified)"""
        
        # Simplified Bayesian optimization
        n_trials = 20
        best_weights = None
        best_score = -np.inf
        history = []
        
        for trial in range(n_trials):
            # Generate random weights
            weights = {}
            remaining_weight = 1.0
            for i, feature in enumerate(feature_columns):
                if i == len(feature_columns) - 1:
                    weights[feature] = remaining_weight
                else:
                    weight = np.random.uniform(0, remaining_weight)
                    weights[feature] = weight
                    remaining_weight -= weight
            
            # Evaluate
            weighted_data = self.apply_weights(data, weights, feature_columns)
            weighted_score = self.get_weighted_score(weighted_data, weights, feature_columns)
            score = abs(weighted_score.corr(target))
            
            history.append({
                "trial": trial,
                "score": score,
                "weights": weights.copy()
            })
            
            if score > best_score:
                best_score = score
                best_weights = weights.copy()
        
        return {
            "method": "bayesian",
            "best_weights": best_weights,
            "best_score": best_score,
            "optimization_history": history
        }

