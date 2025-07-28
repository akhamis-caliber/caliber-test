import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Enumeration of data types for preprocessing"""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATE = "date"
    BOOLEAN = "boolean"

class PreprocessingConfig:
    """Configuration for data preprocessing"""
    
    def __init__(self):
        self.missing_value_strategy = "median"  # "median", "mean", "mode", "drop", "interpolate"
        self.outlier_strategy = "iqr"  # "iqr", "zscore", "isolation_forest", "none"
        self.normalization_strategy = "minmax"  # "minmax", "zscore", "robust", "none"
        self.categorical_encoding = "onehot"  # "onehot", "label", "target", "none"
        self.text_processing = "basic"  # "basic", "advanced", "none"
        self.date_processing = "extract_features"  # "extract_features", "convert_to_numeric", "none"
        self.boolean_processing = "convert_to_int"  # "convert_to_int", "keep_as_is", "none"

def preprocess_data(df: pd.DataFrame, config: Optional[PreprocessingConfig] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Comprehensive data preprocessing for scoring
    
    Args:
        df: Raw dataframe from uploaded file
        config: Preprocessing configuration
        
    Returns:
        Tuple of (preprocessed dataframe, preprocessing metadata)
    """
    if config is None:
        config = PreprocessingConfig()
    
    # Create a copy to avoid modifying original
    processed_df = df.copy()
    preprocessing_metadata = {
        'original_shape': df.shape,
        'original_columns': list(df.columns),
        'preprocessing_steps': [],
        'data_types': {},
        'missing_values': {},
        'outliers_detected': {},
        'transformations_applied': {}
    }
    
    try:
        # Step 1: Detect and validate data types
        data_types = detect_data_types(processed_df)
        preprocessing_metadata['data_types'] = data_types
        preprocessing_metadata['preprocessing_steps'].append('data_type_detection')
        
        # Step 2: Handle missing values
        processed_df, missing_info = handle_missing_values(processed_df, config.missing_value_strategy)
        preprocessing_metadata['missing_values'] = missing_info
        preprocessing_metadata['preprocessing_steps'].append('missing_value_handling')
        
        # Step 3: Handle outliers
        if config.outlier_strategy != "none":
            processed_df, outlier_info = handle_outliers(processed_df, config.outlier_strategy)
            preprocessing_metadata['outliers_detected'] = outlier_info
            preprocessing_metadata['preprocessing_steps'].append('outlier_handling')
        
        # Step 4: Process different data types
        processed_df, transform_info = process_by_data_type(processed_df, data_types, config)
        preprocessing_metadata['transformations_applied'] = transform_info
        preprocessing_metadata['preprocessing_steps'].append('data_type_processing')
        
        # Step 5: Final validation
        processed_df = validate_processed_data(processed_df)
        preprocessing_metadata['preprocessing_steps'].append('final_validation')
        preprocessing_metadata['final_shape'] = processed_df.shape
        
        logger.info(f"Preprocessing completed. Original shape: {df.shape}, Final shape: {processed_df.shape}")
        
        return processed_df, preprocessing_metadata
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {e}")
        raise ValueError(f"Preprocessing failed: {str(e)}")

def detect_data_types(df: pd.DataFrame) -> Dict[str, DataType]:
    """Detect data types for each column"""
    data_types = {}
    
    for col in df.columns:
        # Check for boolean
        if df[col].dtype == bool or (df[col].dtype == object and df[col].isin([True, False, 0, 1]).all()):
            data_types[col] = DataType.BOOLEAN
        # Check for date
        elif df[col].dtype == 'datetime64[ns]' or is_date_column(df[col]):
            data_types[col] = DataType.DATE
        # Check for numerical
        elif df[col].dtype in ['int64', 'float64'] or is_numerical_column(df[col]):
            data_types[col] = DataType.NUMERICAL
        # Check for text
        elif df[col].dtype == object and is_text_column(df[col]):
            data_types[col] = DataType.TEXT
        # Default to categorical
        else:
            data_types[col] = DataType.CATEGORICAL
    
    return data_types

def is_date_column(series: pd.Series) -> bool:
    """Check if a column contains date-like data"""
    if series.dtype == object:
        # Try to parse as datetime
        try:
            pd.to_datetime(series, errors='raise')
            return True
        except:
            return False
    return False

def is_numerical_column(series: pd.Series) -> bool:
    """Check if a column contains numerical data"""
    if series.dtype == object:
        try:
            pd.to_numeric(series, errors='raise')
            return True
        except:
            return False
    return False

def is_text_column(series: pd.Series) -> bool:
    """Check if a column contains text data"""
    if series.dtype == object:
        # Check if average string length is > 10
        avg_length = series.astype(str).str.len().mean()
        return avg_length > 10
    return False

def handle_missing_values(df: pd.DataFrame, strategy: str = "median") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values in the dataset
    
    Args:
        df: Input dataframe
        strategy: Strategy for handling missing values
        
    Returns:
        Tuple of (processed dataframe, missing value metadata)
    """
    result_df = df.copy()
    missing_info = {
        'strategy': strategy,
        'missing_counts': {},
        'missing_percentages': {},
        'actions_taken': {}
    }
    
    # Calculate missing value statistics
    for col in result_df.columns:
        missing_count = result_df[col].isnull().sum()
        missing_percentage = (missing_count / len(result_df)) * 100
        
        missing_info['missing_counts'][col] = int(missing_count)
        missing_info['missing_percentages'][col] = float(missing_percentage)
        
        if missing_count > 0:
            if strategy == "drop":
                # Drop rows with missing values
                result_df = result_df.dropna(subset=[col])
                missing_info['actions_taken'][col] = f"dropped {missing_count} rows"
                
            elif strategy == "median":
                # Fill with median for numerical, mode for categorical
                if result_df[col].dtype in ['int64', 'float64']:
                    fill_value = result_df[col].median()
                    result_df[col].fillna(fill_value, inplace=True)
                    missing_info['actions_taken'][col] = f"filled {missing_count} values with median: {fill_value}"
                else:
                    fill_value = result_df[col].mode()[0] if len(result_df[col].mode()) > 0 else "Unknown"
                    result_df[col].fillna(fill_value, inplace=True)
                    missing_info['actions_taken'][col] = f"filled {missing_count} values with mode: {fill_value}"
                    
            elif strategy == "mean":
                # Fill with mean for numerical, mode for categorical
                if result_df[col].dtype in ['int64', 'float64']:
                    fill_value = result_df[col].mean()
                    result_df[col].fillna(fill_value, inplace=True)
                    missing_info['actions_taken'][col] = f"filled {missing_count} values with mean: {fill_value}"
                else:
                    fill_value = result_df[col].mode()[0] if len(result_df[col].mode()) > 0 else "Unknown"
                    result_df[col].fillna(fill_value, inplace=True)
                    missing_info['actions_taken'][col] = f"filled {missing_count} values with mode: {fill_value}"
                    
            elif strategy == "mode":
                # Fill with mode for all columns
                fill_value = result_df[col].mode()[0] if len(result_df[col].mode()) > 0 else "Unknown"
                result_df[col].fillna(fill_value, inplace=True)
                missing_info['actions_taken'][col] = f"filled {missing_count} values with mode: {fill_value}"
                
            elif strategy == "interpolate":
                # Interpolate missing values
                if result_df[col].dtype in ['int64', 'float64']:
                    result_df[col] = result_df[col].interpolate(method='linear')
                    missing_info['actions_taken'][col] = f"interpolated {missing_count} values"
                else:
                    # For non-numerical, use forward fill then backward fill
                    result_df[col] = result_df[col].fillna(method='ffill').fillna(method='bfill')
                    missing_info['actions_taken'][col] = f"forward/backward filled {missing_count} values"
    
    return result_df, missing_info

def handle_outliers(df: pd.DataFrame, strategy: str = "iqr") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle outliers in the dataset
    
    Args:
        df: Input dataframe
        strategy: Strategy for handling outliers
        
    Returns:
        Tuple of (processed dataframe, outlier metadata)
    """
    from .outliers import OutlierDetector, OutlierMethod, OutlierAction
    
    detector = OutlierDetector()
    outlier_info = {
        'strategy': strategy,
        'outliers_detected': {},
        'actions_taken': {}
    }
    
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if strategy == "iqr":
        method = OutlierMethod.IQR
    elif strategy == "zscore":
        method = OutlierMethod.ZSCORE
    elif strategy == "isolation_forest":
        method = OutlierMethod.ISOLATION_FOREST
    else:
        method = OutlierMethod.IQR
    
    # Detect outliers
    outlier_results = detector.detect_outliers(df, numerical_cols, method)
    outlier_info['outliers_detected'] = outlier_results
    
    # Handle outliers by marking them
    result_df = detector.handle_outliers(df, outlier_results, OutlierAction.MARK)
    
    # Record actions taken
    for col, count in outlier_results['outlier_counts'].items():
        if count > 0:
            outlier_info['actions_taken'][col] = f"marked {count} outliers"
    
    return result_df, outlier_info

def process_by_data_type(df: pd.DataFrame, data_types: Dict[str, DataType], 
                        config: PreprocessingConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Process data based on detected data types
    
    Args:
        df: Input dataframe
        data_types: Dictionary mapping columns to data types
        config: Preprocessing configuration
        
    Returns:
        Tuple of (processed dataframe, transformation metadata)
    """
    result_df = df.copy()
    transform_info = {
        'numerical_processing': {},
        'categorical_processing': {},
        'text_processing': {},
        'date_processing': {},
        'boolean_processing': {}
    }
    
    for col, data_type in data_types.items():
        if data_type == DataType.NUMERICAL:
            result_df, info = process_numerical_column(result_df, col, config.normalization_strategy)
            transform_info['numerical_processing'][col] = info
            
        elif data_type == DataType.CATEGORICAL:
            result_df, info = process_categorical_column(result_df, col, config.categorical_encoding)
            transform_info['categorical_processing'][col] = info
            
        elif data_type == DataType.TEXT:
            result_df, info = process_text_column(result_df, col, config.text_processing)
            transform_info['text_processing'][col] = info
            
        elif data_type == DataType.DATE:
            result_df, info = process_date_column(result_df, col, config.date_processing)
            transform_info['date_processing'][col] = info
            
        elif data_type == DataType.BOOLEAN:
            result_df, info = process_boolean_column(result_df, col, config.boolean_processing)
            transform_info['boolean_processing'][col] = info
    
    return result_df, transform_info

def process_numerical_column(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process numerical column based on strategy"""
    result_df = df.copy()
    info = {'strategy': strategy, 'original_dtype': str(df[column].dtype)}
    
    if strategy == "minmax":
        from .normalize import DataNormalizer
        normalizer = DataNormalizer()
        result_df = normalizer.min_max_scale(result_df, [column])
        info['transformation'] = 'min_max_scaling'
        
    elif strategy == "zscore":
        from .normalize import DataNormalizer
        normalizer = DataNormalizer()
        result_df = normalizer.z_score_normalize(result_df, [column])
        info['transformation'] = 'z_score_normalization'
        
    elif strategy == "robust":
        from .normalize import DataNormalizer
        normalizer = DataNormalizer()
        result_df = normalizer.robust_scale(result_df, [column])
        info['transformation'] = 'robust_scaling'
    
    info['final_dtype'] = str(result_df[column].dtype)
    return result_df, info

def process_categorical_column(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process categorical column based on strategy"""
    result_df = df.copy()
    info = {'strategy': strategy, 'unique_values': int(df[column].nunique())}
    
    if strategy == "onehot":
        # One-hot encoding
        dummies = pd.get_dummies(df[column], prefix=column)
        result_df = pd.concat([result_df, dummies], axis=1)
        result_df.drop(column, axis=1, inplace=True)
        info['transformation'] = 'one_hot_encoding'
        info['new_columns'] = list(dummies.columns)
        
    elif strategy == "label":
        # Label encoding
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        result_df[column] = le.fit_transform(df[column].astype(str))
        info['transformation'] = 'label_encoding'
        info['label_mapping'] = dict(zip(le.classes_, le.transform(le.classes_)))
    
    info['final_dtype'] = str(result_df[column].dtype) if column in result_df.columns else 'removed'
    return result_df, info

def process_text_column(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process text column based on strategy"""
    result_df = df.copy()
    info = {'strategy': strategy, 'avg_length': float(df[column].astype(str).str.len().mean())}
    
    if strategy == "basic":
        # Basic text processing: lowercase, remove special chars
        result_df[column] = df[column].astype(str).str.lower().str.replace(r'[^\w\s]', '', regex=True)
        info['transformation'] = 'basic_text_cleaning'
        
    elif strategy == "advanced":
        # Advanced text processing (placeholder for future implementation)
        result_df[column] = df[column].astype(str).str.lower()
        info['transformation'] = 'advanced_text_processing'
    
    info['final_dtype'] = str(result_df[column].dtype)
    return result_df, info

def process_date_column(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process date column based on strategy"""
    result_df = df.copy()
    info = {'strategy': strategy}
    
    if strategy == "extract_features":
        # Extract date features
        result_df[f'{column}_year'] = pd.to_datetime(df[column]).dt.year
        result_df[f'{column}_month'] = pd.to_datetime(df[column]).dt.month
        result_df[f'{column}_day'] = pd.to_datetime(df[column]).dt.day
        result_df[f'{column}_dayofweek'] = pd.to_datetime(df[column]).dt.dayofweek
        result_df.drop(column, axis=1, inplace=True)
        info['transformation'] = 'date_feature_extraction'
        info['new_columns'] = [f'{column}_year', f'{column}_month', f'{column}_day', f'{column}_dayofweek']
        
    elif strategy == "convert_to_numeric":
        # Convert to numeric (timestamp)
        result_df[column] = pd.to_datetime(df[column]).astype(np.int64) // 10**9
        info['transformation'] = 'timestamp_conversion'
    
    info['final_dtype'] = str(result_df[column].dtype) if column in result_df.columns else 'removed'
    return result_df, info

def process_boolean_column(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process boolean column based on strategy"""
    result_df = df.copy()
    info = {'strategy': strategy}
    
    if strategy == "convert_to_int":
        result_df[column] = df[column].astype(int)
        info['transformation'] = 'boolean_to_int'
    
    info['final_dtype'] = str(result_df[column].dtype)
    return result_df, info

def validate_processed_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate processed data for scoring readiness"""
    # Check for infinite values
    for col in df.select_dtypes(include=[np.number]).columns:
        if np.isinf(df[col]).any():
            logger.warning(f"Found infinite values in column {col}, replacing with NaN")
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    
    # Check for remaining NaN values
    nan_cols = df.columns[df.isnull().any()].tolist()
    if nan_cols:
        logger.warning(f"Found NaN values in columns: {nan_cols}")
        # Fill with 0 for numerical columns
        for col in nan_cols:
            if df[col].dtype in ['int64', 'float64']:
                df[col].fillna(0, inplace=True)
    
    # Ensure all numerical columns are finite
    for col in df.select_dtypes(include=[np.number]).columns:
        if not np.isfinite(df[col]).all():
            logger.error(f"Column {col} still contains non-finite values after processing")
            raise ValueError(f"Data validation failed for column {col}")
    
    return df

# Legacy functions for backward compatibility
def normalize_numerical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    from .normalize import DataNormalizer
    normalizer = DataNormalizer()
    return normalizer.z_score_normalize(df)

def encode_categorical_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    for col in categorical_cols:
        dummies = pd.get_dummies(df[col], prefix=col)
        df = pd.concat([df, dummies], axis=1)
        df.drop(col, axis=1, inplace=True)
    
    return df

def remove_outliers(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    result_df, _ = handle_outliers(df, "zscore")
    return result_df 