import os
import pandas as pd
from werkzeug.utils import secure_filename
from fastapi import UploadFile, HTTPException
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any

ALLOWED_EXTENSIONS = {"csv", "json", "parquet", "xls", "xlsx"}
MAX_FILE_SIZE_MB = 10

# Storage config
STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "local")  # "local" or "s3"
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")

# S3 Configuration
S3_BUCKET = os.environ.get("S3_BUCKET", "caliber-uploads")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client if configured
s3_client = None
if STORAGE_TYPE == "s3" and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=S3_REGION
    )

# Create local upload folder if using local storage
if STORAGE_TYPE == "local":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Campaign-specific column requirements
CAMPAIGN_COLUMN_REQUIREMENTS = {
    "awareness": {
        "required": ["Domain", "Impressions", "CTR"],
        "optional": ["CPM", "Spend", "Publisher", "Channel"],
        "description": "Awareness campaigns require impression and engagement metrics"
    },
    "action": {
        "required": ["Domain", "Impressions", "CTR", "Conversions"],
        "optional": ["CPM", "Spend", "Publisher", "Channel", "Conversion_Rate"],
        "description": "Action campaigns require conversion tracking metrics"
    }
}

# Column name variations for flexible matching
COLUMN_VARIATIONS = {
    "domain": ["domain", "website", "site", "publisher_domain"],
    "impressions": ["impressions", "imp", "views", "served"],
    "ctr": ["ctr", "click_through_rate", "click_rate", "click_through"],
    "conversions": ["conversions", "conv", "conversion", "converted"],
    "cpm": ["cpm", "cost_per_mille", "cost_per_thousand"],
    "spend": ["spend", "cost", "total_spend", "budget"],
    "publisher": ["publisher", "pub", "site_name", "domain_name"],
    "channel": ["channel", "media_type", "ad_type"],
    "conversion_rate": ["conversion_rate", "conv_rate", "conversion_percentage"]
}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file: UploadFile):
    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    file.file.seek(0, os.SEEK_END)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE_MB} MB.")
    return filename

def validate_dataset_columns(df: pd.DataFrame, campaign_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate dataset columns against campaign requirements
    
    Args:
        df: DataFrame to validate
        campaign_metadata: Campaign metadata containing goal and other requirements
        
    Returns:
        Dict containing validation results and suggestions
    """
    validation_result = {
        "valid": True,
        "missing_required": [],
        "missing_optional": [],
        "found_columns": [],
        "suggestions": [],
        "column_mapping": {}
    }
    
    # Get column names from dataframe
    df_columns = [col.lower().strip() for col in df.columns]
    
    # If campaign metadata is provided, validate against campaign requirements
    if campaign_metadata and "goal" in campaign_metadata:
        goal = campaign_metadata["goal"]
        requirements = CAMPAIGN_COLUMN_REQUIREMENTS.get(goal, CAMPAIGN_COLUMN_REQUIREMENTS["awareness"])
        
        # Check required columns
        for required_col in requirements["required"]:
            found = False
            for variation in COLUMN_VARIATIONS.get(required_col.lower(), [required_col.lower()]):
                if variation in df_columns:
                    validation_result["found_columns"].append(required_col)
                    validation_result["column_mapping"][required_col] = variation
                    found = True
                    break
            
            if not found:
                validation_result["missing_required"].append(required_col)
                validation_result["valid"] = False
        
        # Check optional columns
        for optional_col in requirements["optional"]:
            found = False
            for variation in COLUMN_VARIATIONS.get(optional_col.lower(), [optional_col.lower()]):
                if variation in df_columns:
                    validation_result["found_columns"].append(optional_col)
                    validation_result["column_mapping"][optional_col] = variation
                    found = True
                    break
            
            if not found:
                validation_result["missing_optional"].append(optional_col)
        
        # Generate suggestions
        if validation_result["missing_required"]:
            validation_result["suggestions"].append(
                f"Missing required columns for {goal} campaign: {', '.join(validation_result['missing_required'])}"
            )
        
        if validation_result["missing_optional"]:
            validation_result["suggestions"].append(
                f"Consider adding optional columns for better analysis: {', '.join(validation_result['missing_optional'])}"
            )
    
    # Basic validation for common columns
    basic_required = ["domain", "impressions"]
    for col in basic_required:
        if col not in df_columns and not any(variation in df_columns for variation in COLUMN_VARIATIONS.get(col, [col])):
            if col not in validation_result["missing_required"]:
                validation_result["missing_required"].append(col)
                validation_result["valid"] = False
    
    # Check for data quality issues
    if len(df) == 0:
        validation_result["valid"] = False
        validation_result["suggestions"].append("Dataset is empty")
    
    # Check for duplicate columns
    if len(df.columns) != len(set(df.columns)):
        validation_result["suggestions"].append("Dataset contains duplicate column names")
    
    return validation_result

def normalize_column_names(df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Normalize column names based on the mapping
    
    Args:
        df: DataFrame to normalize
        column_mapping: Mapping from standard names to actual column names
        
    Returns:
        DataFrame with normalized column names
    """
    df_normalized = df.copy()
    
    # Rename columns to standard names
    reverse_mapping = {v: k for k, v in column_mapping.items()}
    df_normalized = df_normalized.rename(columns=reverse_mapping)
    
    return df_normalized

def validate_data_types(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate data types and suggest corrections
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dict containing data type validation results
    """
    validation_result = {
        "valid": True,
        "issues": [],
        "suggestions": []
    }
    
    # Check numeric columns
    numeric_columns = ["impressions", "ctr", "conversions", "cpm", "spend"]
    for col in numeric_columns:
        if col in df.columns:
            try:
                pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError):
                validation_result["issues"].append(f"Column '{col}' contains non-numeric values")
                validation_result["suggestions"].append(f"Clean non-numeric values in column '{col}'")
                validation_result["valid"] = False
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    high_missing = missing_counts[missing_counts > len(df) * 0.5]
    if not high_missing.empty:
        validation_result["issues"].append(f"High missing values in columns: {list(high_missing.index)}")
        validation_result["suggestions"].append("Consider removing or imputing missing values")
    
    return validation_result

def save_file(file: UploadFile, filename: str):
    if STORAGE_TYPE == "s3" and s3_client:
        return save_file_to_s3(file, filename)
    else:
        return save_file_local(file, filename)

def save_file_local(file: UploadFile, filename: str):
    """Save file to local storage"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path

def save_file_to_s3(file: UploadFile, filename: str):
    """Save file to S3 storage"""
    try:
        file_content = file.file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=f"uploads/{filename}",
            Body=file_content,
            ContentType=file.content_type
        )
        return f"s3://{S3_BUCKET}/uploads/{filename}"
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

def queue_file_processing(file_path, campaign_id, user_id, report_id=None):
    """
    Queue file processing with enhanced background task for post-campaign flow
    """
    try:
        # Add the worker directory to the Python path
        import sys
        import os
        worker_path = os.path.join(os.path.dirname(__file__), '..', '..', 'worker')
        if worker_path not in sys.path:
            sys.path.append(worker_path)
        
        from tasks import process_and_score_dataset, process_file
        
        # Use enhanced task if report_id is provided (new post-campaign flow)
        if report_id:
            task = process_and_score_dataset.delay(file_path, campaign_id, user_id, report_id)
        else:
            # Fallback to legacy task
            task = process_file.delay(file_path, campaign_id, user_id)
        
        return task.id
    except ImportError as e:
        print(f"Warning: Could not import worker tasks: {e}")
        print("File processing will be skipped. Please ensure Celery worker is running.")
        return None
    except Exception as e:
        print(f"Error queuing file processing: {e}")
        return None 