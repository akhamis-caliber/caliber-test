import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import logging
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope

logger = logging.getLogger(__name__)

class OutlierMethod(Enum):
    """Enumeration of outlier detection methods"""
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    ELLIPTIC_ENVELOPE = "elliptic_envelope"
    MAHALANOBIS = "mahalanobis"
    DBSCAN = "dbscan"

class OutlierAction(Enum):
    """Enumeration of actions to take on outliers"""
    REMOVE = "remove"
    CAP = "cap"
    WINSORIZE = "winsorize"
    MARK = "mark"
    IGNORE = "ignore"

class OutlierDetector:
    """
    Comprehensive outlier detection and handling system
    """
    
    def __init__(self):
        self.detection_results = {}
        self.outlier_reports = {}
        self.detection_configs = {}
    
    def detect_outliers(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                       method: OutlierMethod = OutlierMethod.IQR,
                       **kwargs) -> Dict[str, Any]:
        """
        Detect outliers in the dataset
        
        Args:
            df: Input dataframe
            columns: Columns to analyze (None for all numerical)
            method: Detection method to use
            **kwargs: Method-specific parameters
            
        Returns:
            Dictionary with outlier detection results
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        results = {
            'method': method,
            'columns_analyzed': columns,
            'outlier_indices': {},
            'outlier_counts': {},
            'outlier_percentages': {},
            'detection_params': kwargs
        }
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                try:
                    if method == OutlierMethod.IQR:
                        outlier_indices = self._detect_iqr_outliers(df[col], **kwargs)
                    elif method == OutlierMethod.ZSCORE:
                        outlier_indices = self._detect_zscore_outliers(df[col], **kwargs)
                    elif method == OutlierMethod.ISOLATION_FOREST:
                        outlier_indices = self._detect_isolation_forest_outliers(df, [col], **kwargs)
                    elif method == OutlierMethod.LOCAL_OUTLIER_FACTOR:
                        outlier_indices = self._detect_lof_outliers(df, [col], **kwargs)
                    elif method == OutlierMethod.ELLIPTIC_ENVELOPE:
                        outlier_indices = self._detect_elliptic_envelope_outliers(df, [col], **kwargs)
                    elif method == OutlierMethod.MAHALANOBIS:
                        outlier_indices = self._detect_mahalanobis_outliers(df, [col], **kwargs)
                    else:
                        logger.warning(f"Unknown outlier detection method: {method}")
                        continue
                    
                    results['outlier_indices'][col] = outlier_indices
                    results['outlier_counts'][col] = len(outlier_indices)
                    results['outlier_percentages'][col] = len(outlier_indices) / len(df) * 100
                    
                except Exception as e:
                    logger.error(f"Error detecting outliers in column {col}: {e}")
                    results['outlier_indices'][col] = []
                    results['outlier_counts'][col] = 0
                    results['outlier_percentages'][col] = 0
        
        self.detection_results[method.value] = results
        return results
    
    def _detect_iqr_outliers(self, series: pd.Series, multiplier: float = 1.5) -> List[int]:
        """Detect outliers using IQR method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        return series[outlier_mask].index.tolist()
    
    def _detect_zscore_outliers(self, series: pd.Series, threshold: float = 3.0) -> List[int]:
        """Detect outliers using Z-score method"""
        z_scores = np.abs(stats.zscore(series))
        outlier_mask = z_scores > threshold
        return series[outlier_mask].index.tolist()
    
    def _detect_isolation_forest_outliers(self, df: pd.DataFrame, columns: List[str],
                                        contamination: float = 0.1, **kwargs) -> List[int]:
        """Detect outliers using Isolation Forest"""
        clf = IsolationForest(contamination=contamination, **kwargs)
        predictions = clf.fit_predict(df[columns])
        outlier_mask = predictions == -1
        return df[outlier_mask].index.tolist()
    
    def _detect_lof_outliers(self, df: pd.DataFrame, columns: List[str],
                           contamination: float = 0.1, **kwargs) -> List[int]:
        """Detect outliers using Local Outlier Factor"""
        clf = LocalOutlierFactor(contamination=contamination, **kwargs)
        predictions = clf.fit_predict(df[columns])
        outlier_mask = predictions == -1
        return df[outlier_mask].index.tolist()
    
    def _detect_elliptic_envelope_outliers(self, df: pd.DataFrame, columns: List[str],
                                         contamination: float = 0.1, **kwargs) -> List[int]:
        """Detect outliers using Elliptic Envelope"""
        clf = EllipticEnvelope(contamination=contamination, **kwargs)
        predictions = clf.fit_predict(df[columns])
        outlier_mask = predictions == -1
        return df[outlier_mask].index.tolist()
    
    def _detect_mahalanobis_outliers(self, df: pd.DataFrame, columns: List[str],
                                   threshold: float = 3.0) -> List[int]:
        """Detect outliers using Mahalanobis distance"""
        if len(columns) < 2:
            logger.warning("Mahalanobis distance requires at least 2 columns")
            return []
        
        data = df[columns].values
        mean = np.mean(data, axis=0)
        cov_matrix = np.cov(data.T)
        
        try:
            inv_cov_matrix = np.linalg.inv(cov_matrix)
            mahal_distances = []
            
            for point in data:
                diff = point - mean
                mahal_dist = np.sqrt(diff.T @ inv_cov_matrix @ diff)
                mahal_distances.append(mahal_dist)
            
            outlier_mask = np.array(mahal_distances) > threshold
            return df[outlier_mask].index.tolist()
            
        except np.linalg.LinAlgError:
            logger.warning("Singular covariance matrix, using alternative method")
            return self._detect_zscore_outliers(df[columns[0]], threshold)
    
    def handle_outliers(self, df: pd.DataFrame, outlier_results: Dict[str, Any],
                       action: OutlierAction = OutlierAction.MARK,
                       **kwargs) -> pd.DataFrame:
        """
        Handle detected outliers based on specified action
        
        Args:
            df: Input dataframe
            outlier_results: Results from outlier detection
            action: Action to take on outliers
            **kwargs: Action-specific parameters
            
        Returns:
            Processed dataframe
        """
        result_df = df.copy()
        outlier_indices = outlier_results.get('outlier_indices', {})
        
        for col, indices in outlier_indices.items():
            if col in result_df.columns and indices:
                if action == OutlierAction.REMOVE:
                    result_df = result_df.drop(indices)
                elif action == OutlierAction.CAP:
                    result_df = self._cap_outliers(result_df, col, indices, **kwargs)
                elif action == OutlierAction.WINSORIZE:
                    result_df = self._winsorize_outliers(result_df, col, **kwargs)
                elif action == OutlierAction.MARK:
                    result_df = self._mark_outliers(result_df, col, indices)
                elif action == OutlierAction.IGNORE:
                    # Do nothing, keep outliers as is
                    pass
        
        return result_df
    
    def _cap_outliers(self, df: pd.DataFrame, column: str, outlier_indices: List[int],
                     method: str = 'iqr') -> pd.DataFrame:
        """Cap outliers to specified bounds"""
        series = df[column]
        
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
        elif method == 'percentile':
            lower_bound = series.quantile(0.01)
            upper_bound = series.quantile(0.99)
        else:
            # Use min/max of non-outlier values
            non_outlier_series = series.drop(outlier_indices)
            lower_bound = non_outlier_series.min()
            upper_bound = non_outlier_series.max()
        
        result_df = df.copy()
        result_df.loc[outlier_indices, column] = result_df.loc[outlier_indices, column].clip(
            lower=lower_bound, upper=upper_bound
        )
        
        return result_df
    
    def _winsorize_outliers(self, df: pd.DataFrame, column: str,
                           limits: Tuple[float, float] = (0.05, 0.05)) -> pd.DataFrame:
        """Winsorize outliers using scipy.stats.winsorize"""
        result_df = df.copy()
        result_df[column] = stats.winsorize(df[column], limits=limits)
        return result_df
    
    def _mark_outliers(self, df: pd.DataFrame, column: str, outlier_indices: List[int]) -> pd.DataFrame:
        """Mark outliers with a flag column"""
        result_df = df.copy()
        outlier_flag_col = f"{column}_outlier"
        result_df[outlier_flag_col] = False
        result_df.loc[outlier_indices, outlier_flag_col] = True
        return result_df
    
    def generate_outlier_report(self, outlier_results: Dict[str, Any],
                              df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive outlier report
        
        Args:
            outlier_results: Results from outlier detection
            df: Original dataframe
            
        Returns:
            Detailed outlier report
        """
        report = {
            'summary': {
                'total_columns_analyzed': len(outlier_results['columns_analyzed']),
                'total_outliers_detected': sum(outlier_results['outlier_counts'].values()),
                'detection_method': outlier_results['method'],
                'detection_parameters': outlier_results['detection_params']
            },
            'column_details': {},
            'recommendations': []
        }
        
        for col in outlier_results['columns_analyzed']:
            if col in outlier_results['outlier_counts']:
                outlier_count = outlier_results['outlier_counts'][col]
                outlier_percentage = outlier_results['outlier_percentages'][col]
                outlier_indices = outlier_results['outlier_indices'].get(col, [])
                
                col_report = {
                    'outlier_count': outlier_count,
                    'outlier_percentage': outlier_percentage,
                    'total_records': len(df),
                    'outlier_values': df.loc[outlier_indices, col].tolist() if outlier_indices else [],
                    'outlier_statistics': {
                        'min': df.loc[outlier_indices, col].min() if outlier_indices else None,
                        'max': df.loc[outlier_indices, col].max() if outlier_indices else None,
                        'mean': df.loc[outlier_indices, col].mean() if outlier_indices else None,
                        'std': df.loc[outlier_indices, col].std() if outlier_indices else None
                    } if outlier_indices else {}
                }
                
                report['column_details'][col] = col_report
                
                # Generate recommendations
                if outlier_percentage > 10:
                    report['recommendations'].append(
                        f"High outlier percentage ({outlier_percentage:.1f}%) in {col}. "
                        "Consider investigating data quality or using robust methods."
                    )
                elif outlier_percentage > 5:
                    report['recommendations'].append(
                        f"Moderate outlier percentage ({outlier_percentage:.1f}%) in {col}. "
                        "Consider capping or winsorizing outliers."
                    )
        
        self.outlier_reports[outlier_results['method'].value] = report
        return report
    
    def compare_detection_methods(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                                methods: Optional[List[OutlierMethod]] = None) -> Dict[str, Any]:
        """
        Compare different outlier detection methods
        
        Args:
            df: Input dataframe
            columns: Columns to analyze
            methods: List of methods to compare
            
        Returns:
            Comparison results
        """
        if methods is None:
            methods = [OutlierMethod.IQR, OutlierMethod.ZSCORE, OutlierMethod.ISOLATION_FOREST]
        
        comparison = {
            'methods_compared': [m.value for m in methods],
            'results': {}
        }
        
        for method in methods:
            try:
                results = self.detect_outliers(df, columns, method)
                comparison['results'][method.value] = {
                    'total_outliers': sum(results['outlier_counts'].values()),
                    'outlier_percentages': results['outlier_percentages'],
                    'columns_with_outliers': len([c for c, count in results['outlier_counts'].items() if count > 0])
                }
            except Exception as e:
                logger.error(f"Error comparing method {method}: {e}")
                comparison['results'][method.value] = {'error': str(e)}
        
        return comparison
    
    def get_outlier_statistics(self, df: pd.DataFrame, outlier_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistical summary of outliers
        
        Args:
            df: Input dataframe
            outlier_results: Results from outlier detection
            
        Returns:
            Statistical summary
        """
        stats_summary = {
            'overall_statistics': {
                'total_records': len(df),
                'total_outliers': sum(outlier_results['outlier_counts'].values()),
                'overall_outlier_percentage': sum(outlier_results['outlier_counts'].values()) / len(df) * 100
            },
            'column_statistics': {}
        }
        
        for col in outlier_results['columns_analyzed']:
            if col in outlier_results['outlier_counts']:
                outlier_indices = outlier_results['outlier_indices'].get(col, [])
                if outlier_indices:
                    col_stats = {
                        'outlier_count': len(outlier_indices),
                        'outlier_percentage': len(outlier_indices) / len(df) * 100,
                        'outlier_values': {
                            'min': df.loc[outlier_indices, col].min(),
                            'max': df.loc[outlier_indices, col].max(),
                            'mean': df.loc[outlier_indices, col].mean(),
                            'median': df.loc[outlier_indices, col].median(),
                            'std': df.loc[outlier_indices, col].std()
                        },
                        'non_outlier_values': {
                            'min': df.drop(outlier_indices)[col].min(),
                            'max': df.drop(outlier_indices)[col].max(),
                            'mean': df.drop(outlier_indices)[col].mean(),
                            'median': df.drop(outlier_indices)[col].median(),
                            'std': df.drop(outlier_indices)[col].std()
                        }
                    }
                    stats_summary['column_statistics'][col] = col_stats
        
        return stats_summary 