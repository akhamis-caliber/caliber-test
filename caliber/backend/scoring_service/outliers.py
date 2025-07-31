import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope
from scipy import stats
import warnings

from common.exceptions import ValidationError

logger = logging.getLogger(__name__)

class OutlierDetector:
    """Detector for identifying and handling outliers in scoring data"""
    
    def __init__(self):
        self.isolation_forest = None
        self.local_outlier_factor = None
        self.elliptic_envelope = None
        self.detected_outliers = {}
    
    def detect_outliers(
        self,
        data: pd.DataFrame,
        method: str = "isolation_forest",
        columns: Optional[List[str]] = None,
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """Detect outliers in the data using various methods"""
        
        try:
            if columns is None:
                columns = data.select_dtypes(include=[np.number]).columns.tolist()
            
            if method == "isolation_forest":
                return self._detect_with_isolation_forest(data, columns, contamination)
            elif method == "local_outlier_factor":
                return self._detect_with_lof(data, columns, contamination)
            elif method == "elliptic_envelope":
                return self._detect_with_elliptic_envelope(data, columns, contamination)
            elif method == "zscore":
                return self._detect_with_zscore(data, columns)
            elif method == "iqr":
                return self._detect_with_iqr(data, columns)
            elif method == "combined":
                return self._detect_with_combined_methods(data, columns, contamination)
            else:
                raise ValidationError(f"Unknown outlier detection method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to detect outliers: {e}")
            raise ValidationError(f"Outlier detection failed: {str(e)}")
    
    def remove_outliers(
        self,
        data: pd.DataFrame,
        outlier_indices: List[int],
        method: str = "drop"
    ) -> pd.DataFrame:
        """Remove outliers from the data"""
        
        try:
            if method == "drop":
                return data.drop(outlier_indices).reset_index(drop=True)
            elif method == "cap":
                return self._cap_outliers(data, outlier_indices)
            elif method == "winsorize":
                return self._winsorize_outliers(data, outlier_indices)
            else:
                raise ValidationError(f"Unknown outlier removal method: {method}")
                
        except Exception as e:
            logger.error(f"Failed to remove outliers: {e}")
            raise ValidationError(f"Outlier removal failed: {str(e)}")
    
    def analyze_outliers(
        self,
        data: pd.DataFrame,
        outlier_indices: List[int],
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze the characteristics of detected outliers"""
        
        try:
            if columns is None:
                columns = data.select_dtypes(include=[np.number]).columns.tolist()
            
            outlier_data = data.iloc[outlier_indices]
            non_outlier_data = data.drop(outlier_indices)
            
            analysis = {
                "total_outliers": len(outlier_indices),
                "outlier_percentage": len(outlier_indices) / len(data) * 100,
                "columns_analysis": {},
                "summary": {}
            }
            
            # Analyze each column
            for column in columns:
                if column in data.columns:
                    col_analysis = self._analyze_column_outliers(
                        data[column], outlier_data[column], non_outlier_data[column]
                    )
                    analysis["columns_analysis"][column] = col_analysis
            
            # Generate summary
            analysis["summary"] = self._generate_outlier_summary(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze outliers: {e}")
            raise ValidationError(f"Outlier analysis failed: {str(e)}")
    
    def get_outlier_recommendations(
        self,
        outlier_analysis: Dict[str, Any],
        data_shape: Tuple[int, int]
    ) -> List[str]:
        """Get recommendations for handling outliers"""
        
        recommendations = []
        
        total_outliers = outlier_analysis.get("total_outliers", 0)
        outlier_percentage = outlier_analysis.get("outlier_percentage", 0)
        
        if outlier_percentage > 20:
            recommendations.append("High outlier percentage detected. Consider investigating data quality issues.")
        elif outlier_percentage > 10:
            recommendations.append("Moderate outlier percentage. Review outlier handling strategy.")
        else:
            recommendations.append("Low outlier percentage. Standard outlier handling should be sufficient.")
        
        # Check for specific patterns
        columns_analysis = outlier_analysis.get("columns_analysis", {})
        for column, analysis in columns_analysis.items():
            if analysis.get("outlier_mean", 0) > analysis.get("non_outlier_mean", 0) * 3:
                recommendations.append(f"Column '{column}' has extreme outliers. Consider capping or winsorizing.")
        
        if total_outliers > data_shape[0] * 0.05:
            recommendations.append("Consider using robust statistical methods that are less sensitive to outliers.")
        
        return recommendations
    
    def _detect_with_isolation_forest(
        self,
        data: pd.DataFrame,
        columns: List[str],
        contamination: float
    ) -> Dict[str, Any]:
        """Detect outliers using Isolation Forest"""
        
        X = data[columns].fillna(data[columns].median())
        
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42
        )
        
        outlier_labels = self.isolation_forest.fit_predict(X)
        outlier_indices = np.where(outlier_labels == -1)[0].tolist()
        
        return {
            "method": "isolation_forest",
            "outlier_indices": outlier_indices,
            "outlier_count": len(outlier_indices),
            "contamination": contamination,
            "model": self.isolation_forest
        }
    
    def _detect_with_lof(
        self,
        data: pd.DataFrame,
        columns: List[str],
        contamination: float
    ) -> Dict[str, Any]:
        """Detect outliers using Local Outlier Factor"""
        
        X = data[columns].fillna(data[columns].median())
        
        self.local_outlier_factor = LocalOutlierFactor(
            contamination=contamination,
            n_neighbors=20
        )
        
        outlier_labels = self.local_outlier_factor.fit_predict(X)
        outlier_indices = np.where(outlier_labels == -1)[0].tolist()
        
        return {
            "method": "local_outlier_factor",
            "outlier_indices": outlier_indices,
            "outlier_count": len(outlier_indices),
            "contamination": contamination,
            "model": self.local_outlier_factor
        }
    
    def _detect_with_elliptic_envelope(
        self,
        data: pd.DataFrame,
        columns: List[str],
        contamination: float
    ) -> Dict[str, Any]:
        """Detect outliers using Elliptic Envelope"""
        
        X = data[columns].fillna(data[columns].median())
        
        self.elliptic_envelope = EllipticEnvelope(
            contamination=contamination,
            random_state=42
        )
        
        outlier_labels = self.elliptic_envelope.fit_predict(X)
        outlier_indices = np.where(outlier_labels == -1)[0].tolist()
        
        return {
            "method": "elliptic_envelope",
            "outlier_indices": outlier_indices,
            "outlier_count": len(outlier_indices),
            "contamination": contamination,
            "model": self.elliptic_envelope
        }
    
    def _detect_with_zscore(
        self,
        data: pd.DataFrame,
        columns: List[str],
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """Detect outliers using Z-score method"""
        
        outlier_indices = []
        
        for column in columns:
            if column in data.columns:
                z_scores = np.abs(stats.zscore(data[column].fillna(data[column].median())))
                column_outliers = np.where(z_scores > threshold)[0]
                outlier_indices.extend(column_outliers.tolist())
        
        # Remove duplicates
        outlier_indices = list(set(outlier_indices))
        
        return {
            "method": "zscore",
            "outlier_indices": outlier_indices,
            "outlier_count": len(outlier_indices),
            "threshold": threshold
        }
    
    def _detect_with_iqr(
        self,
        data: pd.DataFrame,
        columns: List[str],
        multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """Detect outliers using IQR method"""
        
        outlier_indices = []
        
        for column in columns:
            if column in data.columns:
                Q1 = data[column].quantile(0.25)
                Q3 = data[column].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - multiplier * IQR
                upper_bound = Q3 + multiplier * IQR
                
                column_outliers = data[
                    (data[column] < lower_bound) | (data[column] > upper_bound)
                ].index.tolist()
                
                outlier_indices.extend(column_outliers)
        
        # Remove duplicates
        outlier_indices = list(set(outlier_indices))
        
        return {
            "method": "iqr",
            "outlier_indices": outlier_indices,
            "outlier_count": len(outlier_indices),
            "multiplier": multiplier
        }
    
    def _detect_with_combined_methods(
        self,
        data: pd.DataFrame,
        columns: List[str],
        contamination: float
    ) -> Dict[str, Any]:
        """Detect outliers using multiple methods and combine results"""
        
        # Use multiple methods
        if_results = self._detect_with_isolation_forest(data, columns, contamination)
        lof_results = self._detect_with_lof(data, columns, contamination)
        zscore_results = self._detect_with_zscore(data, columns)
        
        # Combine outlier indices (union)
        all_outliers = set(if_results["outlier_indices"])
        all_outliers.update(lof_results["outlier_indices"])
        all_outliers.update(zscore_results["outlier_indices"])
        
        outlier_indices = list(all_outliers)
        
        return {
            "method": "combined",
            "outlier_indices": outlier_indices,
            "outlier_count": len(outlier_indices),
            "methods_used": ["isolation_forest", "local_outlier_factor", "zscore"],
            "individual_results": {
                "isolation_forest": if_results,
                "local_outlier_factor": lof_results,
                "zscore": zscore_results
            }
        }
    
    def _cap_outliers(
        self,
        data: pd.DataFrame,
        outlier_indices: List[int],
        percentile_low: float = 1.0,
        percentile_high: float = 99.0
    ) -> pd.DataFrame:
        """Cap outliers to percentile bounds"""
        
        data_copy = data.copy()
        
        for column in data_copy.select_dtypes(include=[np.number]).columns:
            if column in data_copy.columns:
                lower_bound = data_copy[column].quantile(percentile_low / 100)
                upper_bound = data_copy[column].quantile(percentile_high / 100)
                
                data_copy[column] = data_copy[column].clip(lower=lower_bound, upper=upper_bound)
        
        return data_copy
    
    def _winsorize_outliers(
        self,
        data: pd.DataFrame,
        outlier_indices: List[int],
        limits: Tuple[float, float] = (0.05, 0.05)
    ) -> pd.DataFrame:
        """Winsorize outliers"""
        
        data_copy = data.copy()
        
        for column in data_copy.select_dtypes(include=[np.number]).columns:
            if column in data_copy.columns:
                data_copy[column] = stats.mstats.winsorize(
                    data_copy[column], limits=limits
                )
        
        return data_copy
    
    def _analyze_column_outliers(
        self,
        full_column: pd.Series,
        outlier_column: pd.Series,
        non_outlier_column: pd.Series
    ) -> Dict[str, Any]:
        """Analyze outliers for a specific column"""
        
        return {
            "outlier_count": len(outlier_column),
            "outlier_mean": outlier_column.mean(),
            "outlier_std": outlier_column.std(),
            "outlier_min": outlier_column.min(),
            "outlier_max": outlier_column.max(),
            "non_outlier_mean": non_outlier_column.mean(),
            "non_outlier_std": non_outlier_column.std(),
            "mean_difference": outlier_column.mean() - non_outlier_column.mean(),
            "std_ratio": outlier_column.std() / non_outlier_column.std() if non_outlier_column.std() > 0 else 0
        }
    
    def _generate_outlier_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of outlier analysis"""
        
        total_outliers = analysis.get("total_outliers", 0)
        outlier_percentage = analysis.get("outlier_percentage", 0)
        
        # Find columns with most outliers
        columns_analysis = analysis.get("columns_analysis", {})
        outlier_counts = {
            col: info.get("outlier_count", 0) 
            for col, info in columns_analysis.items()
        }
        
        top_outlier_columns = sorted(
            outlier_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_outliers": total_outliers,
            "outlier_percentage": outlier_percentage,
            "top_outlier_columns": top_outlier_columns,
            "severity": self._assess_outlier_severity(outlier_percentage)
        }
    
    def _assess_outlier_severity(self, outlier_percentage: float) -> str:
        """Assess the severity of outlier percentage"""
        
        if outlier_percentage > 20:
            return "high"
        elif outlier_percentage > 10:
            return "moderate"
        elif outlier_percentage > 5:
            return "low"
        else:
            return "minimal"

