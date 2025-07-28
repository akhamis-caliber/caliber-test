# Scoring Engine Service

A comprehensive scoring engine for data analysis and performance evaluation with advanced preprocessing, normalization, weighting, outlier detection, and explanation capabilities.

## Overview

The scoring engine provides a complete pipeline for transforming raw data into meaningful scores with detailed explanations and insights. It's designed to be flexible, configurable, and production-ready.

## Components

### 1. Preprocessing (`preprocess.py`)

Handles data cleaning and validation:

- Missing value handling
- Type conversion and normalization
- Categorical variable encoding
- Outlier removal

### 2. Normalization (`normalize.py`)

Provides multiple data scaling methods:

- Min-max scaling
- Z-score normalization
- Robust scaling
- Power transformations
- Quantile transformations
- Custom scaling methods

### 3. Weighting (`weighting.py`)

Manages score calculation and weighting:

- Campaign-specific weights
- Multiple weighting strategies (linear, exponential, logarithmic)
- Support for different metric types (continuous, binary, categorical, etc.)
- Dynamic weight adjustment
- Composite scoring

### 4. Outlier Detection (`outliers.py`)

Comprehensive outlier detection and handling:

- Multiple detection methods (IQR, Z-score, Isolation Forest, etc.)
- Various handling strategies (remove, cap, winsorize, mark)
- Statistical analysis and reporting
- Method comparison

### 5. Explanation (`explain.py`)

Generates insights and explanations:

- Score breakdown analysis
- Factor analysis
- Comparative analysis
- AI-powered insights (OpenAI integration)
- Actionable recommendations

### 6. Main Orchestrator (`scoring.py`)

Integrates all components into a unified scoring engine:

- Complete scoring pipeline
- Configuration management
- Result aggregation
- History tracking

## Quick Start

### Basic Usage

```python
from scoring_service import ScoringEngine

# Initialize the scoring engine
engine = ScoringEngine()

# Create sample data
import pandas as pd
df = pd.DataFrame({
    'revenue': [1000000, 2000000, 1500000],
    'profit_margin': [15, 20, 18],
    'growth_rate': [10, 15, 12]
})

# Configure scoring process
config = {
    'outlier_config': {
        'method': 'iqr',
        'action': 'mark'
    },
    'normalization_config': {
        'method': 'zscore'
    },
    'weighting_config': {
        'strategy': 'linear',
        'metrics': ['revenue', 'profit_margin', 'growth_rate']
    }
}

# Calculate scores
campaign_id = 1
results = engine.calculate_scores(df, campaign_id, config)

# Access results
scored_df = results['scored_dataframe']
explanation = results['explanation']
outlier_report = results['outlier_report']
```

### Individual Component Usage

#### Preprocessing

```python
from scoring_service import preprocess_data

processed_df = preprocess_data(raw_df)
```

#### Normalization

```python
from scoring_service import DataNormalizer

normalizer = DataNormalizer()
normalized_df = normalizer.z_score_normalize(df, columns=['col1', 'col2'])
```

#### Outlier Detection

```python
from scoring_service import OutlierDetector, OutlierMethod, OutlierAction

detector = OutlierDetector()
results = detector.detect_outliers(df, method=OutlierMethod.IQR)
handled_df = detector.handle_outliers(df, results, action=OutlierAction.MARK)
```

#### Weighting

```python
from scoring_service import ScoreWeightingEngine, WeightingStrategy, MetricType

engine = ScoreWeightingEngine()
engine.set_campaign_weights(1, {'metric1': 0.5, 'metric2': 0.5})
scores = engine.calculate_weighted_score(df, 1, ['metric1', 'metric2'])
```

#### Explanation

```python
from scoring_service import ScoreExplainer, ExplanationConfig, ExplanationType

explainer = ScoreExplainer()
config = ExplanationConfig(
    explanation_type=ExplanationType.SCORE_BREAKDOWN,
    include_metrics=['metric1', 'metric2']
)
explanation = explainer.generate_score_explanation(df, scores, config)
```

## Configuration Options

### Outlier Detection Methods

- `IQR`: Interquartile Range method
- `ZSCORE`: Z-score method
- `ISOLATION_FOREST`: Machine learning-based detection
- `LOCAL_OUTLIER_FACTOR`: Density-based detection
- `ELLIPTIC_ENVELOPE`: Gaussian distribution-based detection
- `MAHALANOBIS`: Multivariate distance-based detection

### Normalization Methods

- `zscore`: Standardization (mean=0, std=1)
- `minmax`: Min-max scaling (0-1 range)
- `robust`: Robust scaling (median-based)
- `power`: Power transformations
- `quantile`: Quantile-based transformations

### Weighting Strategies

- `LINEAR`: Simple linear combination
- `EXPONENTIAL`: Exponential weighting
- `LOGARITHMIC`: Logarithmic weighting
- `CUSTOM`: Custom weighting function

### Explanation Types

- `SCORE_BREAKDOWN`: Detailed score analysis
- `FACTOR_ANALYSIS`: Factor contribution analysis
- `COMPARATIVE_ANALYSIS`: Benchmark comparisons
- `TREND_ANALYSIS`: Temporal analysis
- `RECOMMENDATIONS`: Actionable recommendations

## Advanced Features

### AI-Powered Insights

The explanation module can integrate with OpenAI's GPT models for enhanced insights:

```python
explainer = ScoreExplainer(openai_api_key="your-api-key")
# AI insights will be automatically generated
```

### Method Comparison

Compare different scoring configurations:

```python
methods = [
    {'outlier_config': {'method': 'iqr'}, 'normalization_config': {'method': 'zscore'}},
    {'outlier_config': {'method': 'zscore'}, 'normalization_config': {'method': 'minmax'}}
]
comparison = engine.compare_scoring_methods(df, campaign_id, methods)
```

### Custom Metric Types

Configure different metric types for specialized handling:

```python
engine.configure_metric('revenue', MetricType.CONTINUOUS, {'method': 'minmax'})
engine.configure_metric('is_public', MetricType.BINARY, {'true_value': 1})
engine.configure_metric('industry', MetricType.CATEGORICAL, {'value_mapping': {...}})
```

## Data Requirements

### Input Data Format

- Pandas DataFrame
- Numerical columns for scoring metrics
- Categorical columns supported
- Missing values handled automatically

### Required Columns

- At least one numerical column for scoring
- Unique identifier column recommended
- Campaign-specific requirements may apply

## Output Format

### Scoring Results

```python
{
    'scored_dataframe': pd.DataFrame,  # Original data + scores
    'metadata': {
        'campaign_id': int,
        'total_records': int,
        'processing_time': float,
        'average_score': float,
        'score_range': str,
        'outlier_summary': dict,
        'normalization_summary': dict,
        'weighting_summary': dict
    },
    'explanation': dict,  # Detailed explanation
    'outlier_report': dict,  # Outlier analysis
    'config_used': dict  # Configuration applied
}
```

### Explanation Output

```python
{
    'timestamp': str,
    'explanation_type': str,
    'summary': dict,
    'details': dict,
    'recommendations': list,
    'metadata': dict,
    'ai_insights': dict  # If OpenAI enabled
}
```

## Error Handling

The scoring engine includes comprehensive error handling:

- Input validation
- Graceful degradation for missing components
- Detailed error messages
- Logging for debugging

## Performance Considerations

- Large datasets: Use batch processing for datasets > 100k records
- Memory usage: Monitor memory consumption for very large datasets
- Processing time: Scales linearly with dataset size
- Parallel processing: Consider parallelization for multiple campaigns

## Dependencies

### Required

- pandas >= 1.3.0
- numpy >= 1.20.0
- scikit-learn >= 1.0.0
- scipy >= 1.7.0

### Optional

- openai >= 0.27.0 (for AI insights)

## Installation

```bash
# Install required dependencies
pip install pandas numpy scikit-learn scipy

# Optional: Install OpenAI for AI insights
pip install openai
```

## Examples

See `example_usage.py` for comprehensive examples demonstrating all features.

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure backward compatibility

## License

This project is part of the Caliber platform and follows the same licensing terms.
