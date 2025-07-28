import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.preprocessing import PowerTransformer, QuantileTransformer
import logging

logger = logging.getLogger(__name__)

class DataNormalizer:
    """
    Comprehensive data normalization class with multiple scaling methods
    """
    
    def __init__(self):
        self.scalers = {}
        self.scaling_params = {}
    
    def min_max_scale(self, df: pd.DataFrame, columns: Optional[List[str]] = None, 
                     feature_range: Tuple[float, float] = (0, 1)) -> pd.DataFrame:
        """
        Apply min-max scaling to numerical columns
        
        Args:
            df: Input dataframe
            columns: List of columns to scale (None for all numerical)
            feature_range: Range for scaling (min, max)
            
        Returns:
            Scaled dataframe
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                scaler = MinMaxScaler(feature_range=feature_range)
                result_df[col] = scaler.fit_transform(df[[col]])
                self.scalers[f'minmax_{col}'] = scaler
                self.scaling_params[f'minmax_{col}'] = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'feature_range': feature_range
                }
        
        return result_df
    
    def z_score_normalize(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                         with_mean: bool = True, with_std: bool = True) -> pd.DataFrame:
        """
        Apply z-score normalization (standardization)
        
        Args:
            df: Input dataframe
            columns: List of columns to normalize (None for all numerical)
            with_mean: Whether to center the data
            with_std: Whether to scale to unit variance
            
        Returns:
            Normalized dataframe
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                scaler = StandardScaler(with_mean=with_mean, with_std=with_std)
                result_df[col] = scaler.fit_transform(df[[col]])
                self.scalers[f'zscore_{col}'] = scaler
                self.scaling_params[f'zscore_{col}'] = {
                    'mean': df[col].mean() if with_mean else 0,
                    'std': df[col].std() if with_std else 1
                }
        
        return result_df
    
    def robust_scale(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                    with_centering: bool = True, with_scaling: bool = True,
                    quantile_range: Tuple[float, float] = (25.0, 75.0)) -> pd.DataFrame:
        """
        Apply robust scaling (insensitive to outliers)
        
        Args:
            df: Input dataframe
            columns: List of columns to scale (None for all numerical)
            with_centering: Whether to center the data
            with_scaling: Whether to scale the data
            quantile_range: Quantile range for scaling
            
        Returns:
            Scaled dataframe
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                scaler = RobustScaler(
                    with_centering=with_centering,
                    with_scaling=with_scaling,
                    quantile_range=quantile_range
                )
                result_df[col] = scaler.fit_transform(df[[col]])
                self.scalers[f'robust_{col}'] = scaler
                self.scaling_params[f'robust_{col}'] = {
                    'center': df[col].median() if with_centering else 0,
                    'scale': (df[col].quantile(quantile_range[1]/100) - 
                             df[col].quantile(quantile_range[0]/100)) if with_scaling else 1
                }
        
        return result_df
    
    def power_transform(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                       method: str = 'yeo-johnson') -> pd.DataFrame:
        """
        Apply power transformation to make data more Gaussian-like
        
        Args:
            df: Input dataframe
            columns: List of columns to transform (None for all numerical)
            method: 'yeo-johnson' or 'box-cox'
            
        Returns:
            Transformed dataframe
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                try:
                    scaler = PowerTransformer(method=method)
                    result_df[col] = scaler.fit_transform(df[[col]])
                    self.scalers[f'power_{col}'] = scaler
                    self.scaling_params[f'power_{col}'] = {
                        'method': method,
                        'lambdas': scaler.lambdas_.tolist()
                    }
                except Exception as e:
                    logger.warning(f"Power transform failed for column {col}: {e}")
                    # Keep original values if transformation fails
                    continue
        
        return result_df
    
    def quantile_transform(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                          n_quantiles: int = 1000, output_distribution: str = 'uniform',
                          ignore_implicit_zeros: bool = False) -> pd.DataFrame:
        """
        Apply quantile transformation
        
        Args:
            df: Input dataframe
            columns: List of columns to transform (None for all numerical)
            n_quantiles: Number of quantiles to compute
            output_distribution: 'uniform' or 'normal'
            ignore_implicit_zeros: Whether to ignore implicit zeros
            
        Returns:
            Transformed dataframe
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                scaler = QuantileTransformer(
                    n_quantiles=n_quantiles,
                    output_distribution=output_distribution,
                    ignore_implicit_zeros=ignore_implicit_zeros
                )
                result_df[col] = scaler.fit_transform(df[[col]])
                self.scalers[f'quantile_{col}'] = scaler
                self.scaling_params[f'quantile_{col}'] = {
                    'n_quantiles': n_quantiles,
                    'output_distribution': output_distribution
                }
        
        return result_df
    
    def custom_scale(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                    method: str = 'log', **kwargs) -> pd.DataFrame:
        """
        Apply custom scaling methods
        
        Args:
            df: Input dataframe
            columns: List of columns to scale (None for all numerical)
            method: 'log', 'sqrt', 'reciprocal', 'square'
            **kwargs: Additional parameters for scaling
            
        Returns:
            Scaled dataframe
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['int64', 'float64']:
                try:
                    if method == 'log':
                        # Add small constant to avoid log(0)
                        epsilon = kwargs.get('epsilon', 1e-8)
                        result_df[col] = np.log(df[col] + epsilon)
                    elif method == 'sqrt':
                        result_df[col] = np.sqrt(np.abs(df[col]))
                    elif method == 'reciprocal':
                        # Add small constant to avoid division by zero
                        epsilon = kwargs.get('epsilon', 1e-8)
                        result_df[col] = 1 / (df[col] + epsilon)
                    elif method == 'square':
                        result_df[col] = df[col] ** 2
                    else:
                        logger.warning(f"Unknown custom scaling method: {method}")
                        continue
                    
                    self.scaling_params[f'custom_{method}_{col}'] = {
                        'method': method,
                        'kwargs': kwargs
                    }
                    
                except Exception as e:
                    logger.warning(f"Custom scaling failed for column {col}: {e}")
                    continue
        
        return result_df
    
    def normalize_by_group(self, df: pd.DataFrame, group_column: str, 
                          value_columns: List[str], method: str = 'zscore') -> pd.DataFrame:
        """
        Normalize values within groups
        
        Args:
            df: Input dataframe
            group_column: Column to group by
            value_columns: Columns to normalize
            method: Normalization method ('zscore', 'minmax', 'robust')
            
        Returns:
            Normalized dataframe
        """
        result_df = df.copy()
        
        for group_name, group_data in df.groupby(group_column):
            group_indices = group_data.index
            
            for col in value_columns:
                if col in group_data.columns and group_data[col].dtype in ['int64', 'float64']:
                    if method == 'zscore':
                        mean_val = group_data[col].mean()
                        std_val = group_data[col].std()
                        if std_val > 0:
                            result_df.loc[group_indices, col] = (group_data[col] - mean_val) / std_val
                    elif method == 'minmax':
                        min_val = group_data[col].min()
                        max_val = group_data[col].max()
                        if max_val > min_val:
                            result_df.loc[group_indices, col] = (group_data[col] - min_val) / (max_val - min_val)
                    elif method == 'robust':
                        median_val = group_data[col].median()
                        q75, q25 = group_data[col].quantile([0.75, 0.25])
                        iqr = q75 - q25
                        if iqr > 0:
                            result_df.loc[group_indices, col] = (group_data[col] - median_val) / iqr
        
        return result_df
    
    def get_scaling_summary(self) -> Dict[str, Any]:
        """Get summary of applied scaling operations"""
        return {
            'applied_scalers': list(self.scalers.keys()),
            'scaling_params': self.scaling_params,
            'total_operations': len(self.scalers)
        }
    
    def inverse_transform(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Apply inverse transformation to scaled data
        
        Args:
            df: Scaled dataframe
            columns: Columns to inverse transform (None for all available)
            
        Returns:
            Original scale dataframe
        """
        if columns is None:
            columns = [key.split('_', 1)[1] for key in self.scalers.keys()]
        
        result_df = df.copy()
        
        for col in columns:
            for scaler_key, scaler in self.scalers.items():
                if scaler_key.endswith(f'_{col}'):
                    try:
                        result_df[col] = scaler.inverse_transform(df[[col]])
                        break
                    except Exception as e:
                        logger.warning(f"Inverse transform failed for {col}: {e}")
                        continue
        
        return result_df 