#!/usr/bin/env python3
"""
Example usage of the comprehensive scoring engine

This script demonstrates how to use all the scoring engine components:
- Data preprocessing
- Normalization
- Weighting
- Outlier detection
- Score explanation
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

# Import our scoring components
from scoring import ScoringEngine
from preprocess import preprocess_data
from normalize import DataNormalizer
from weighting import ScoreWeightingEngine, WeightingStrategy, MetricType
from outliers import OutlierDetector, OutlierMethod, OutlierAction
from explain import ScoreExplainer, ExplanationConfig, ExplanationType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_data() -> pd.DataFrame:
    """Create sample data for demonstration"""
    np.random.seed(42)
    
    # Generate sample data with various characteristics
    n_records = 1000
    
    data = {
        'company_id': range(1, n_records + 1),
        'revenue': np.random.lognormal(10, 1, n_records),
        'profit_margin': np.random.beta(2, 5, n_records) * 100,
        'growth_rate': np.random.normal(15, 10, n_records),
        'market_share': np.random.beta(1, 10, n_records) * 100,
        'customer_satisfaction': np.random.normal(75, 15, n_records),
        'employee_count': np.random.poisson(500, n_records),
        'industry': np.random.choice(['Technology', 'Healthcare', 'Finance', 'Retail'], n_records),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_records),
        'is_public': np.random.choice([0, 1], n_records, p=[0.7, 0.3])
    }
    
    # Add some outliers for demonstration
    data['revenue'][0] = data['revenue'].max() * 5  # Extreme outlier
    data['profit_margin'][1] = -50  # Negative outlier
    data['growth_rate'][2] = 200  # High outlier
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    df.loc[10:15, 'customer_satisfaction'] = np.nan
    df.loc[20:25, 'market_share'] = np.nan
    
    return df

def demonstrate_preprocessing():
    """Demonstrate data preprocessing"""
    logger.info("=== Data Preprocessing Demo ===")
    
    # Create sample data
    df = create_sample_data()
    logger.info(f"Original data shape: {df.shape}")
    logger.info(f"Missing values:\n{df.isnull().sum()}")
    
    # Preprocess data
    processed_df = preprocess_data(df)
    logger.info(f"Processed data shape: {processed_df.shape}")
    logger.info(f"Missing values after preprocessing:\n{processed_df.isnull().sum()}")
    
    return processed_df

def demonstrate_normalization():
    """Demonstrate data normalization"""
    logger.info("\n=== Data Normalization Demo ===")
    
    df = create_sample_data()
    normalizer = DataNormalizer()
    
    # Demonstrate different normalization methods
    numerical_cols = ['revenue', 'profit_margin', 'growth_rate', 'market_share', 'customer_satisfaction']
    
    # Z-score normalization
    zscore_df = normalizer.z_score_normalize(df, columns=numerical_cols)
    logger.info("Z-score normalization applied")
    
    # Min-max scaling
    minmax_df = normalizer.min_max_scale(df, columns=numerical_cols)
    logger.info("Min-max scaling applied")
    
    # Robust scaling
    robust_df = normalizer.robust_scale(df, columns=numerical_cols)
    logger.info("Robust scaling applied")
    
    # Get scaling summary
    summary = normalizer.get_scaling_summary()
    logger.info(f"Scaling summary: {len(summary['applied_scalers'])} operations performed")
    
    return normalizer

def demonstrate_outlier_detection():
    """Demonstrate outlier detection"""
    logger.info("\n=== Outlier Detection Demo ===")
    
    df = create_sample_data()
    detector = OutlierDetector()
    
    # Detect outliers using different methods
    numerical_cols = ['revenue', 'profit_margin', 'growth_rate', 'market_share', 'customer_satisfaction']
    
    # IQR method
    iqr_results = detector.detect_outliers(df, columns=numerical_cols, method=OutlierMethod.IQR)
    logger.info(f"IQR outliers detected: {sum(iqr_results['outlier_counts'].values())}")
    
    # Z-score method
    zscore_results = detector.detect_outliers(df, columns=numerical_cols, method=OutlierMethod.ZSCORE)
    logger.info(f"Z-score outliers detected: {sum(zscore_results['outlier_counts'].values())}")
    
    # Isolation Forest
    iso_results = detector.detect_outliers(df, columns=numerical_cols, method=OutlierMethod.ISOLATION_FOREST)
    logger.info(f"Isolation Forest outliers detected: {sum(iso_results['outlier_counts'].values())}")
    
    # Generate outlier report
    report = detector.generate_outlier_report(iqr_results, df)
    logger.info(f"Outlier report generated with {len(report['recommendations'])} recommendations")
    
    # Handle outliers
    handled_df = detector.handle_outliers(df, iqr_results, action=OutlierAction.MARK)
    logger.info(f"Outliers marked in dataframe")
    
    return detector, handled_df

def demonstrate_weighting():
    """Demonstrate weighting engine"""
    logger.info("\n=== Weighting Engine Demo ===")
    
    df = create_sample_data()
    weighting_engine = ScoreWeightingEngine()
    
    # Configure campaign weights
    campaign_id = 1
    weights = {
        'revenue': 0.25,
        'profit_margin': 0.20,
        'growth_rate': 0.20,
        'market_share': 0.15,
        'customer_satisfaction': 0.20
    }
    
    weighting_engine.set_campaign_weights(campaign_id, weights)
    
    # Configure metrics
    weighting_engine.configure_metric('revenue', MetricType.CONTINUOUS, {'method': 'minmax'})
    weighting_engine.configure_metric('profit_margin', MetricType.PERCENTAGE, {})
    weighting_engine.configure_metric('growth_rate', MetricType.CONTINUOUS, {'method': 'zscore'})
    weighting_engine.configure_metric('market_share', MetricType.PERCENTAGE, {})
    weighting_engine.configure_metric('customer_satisfaction', MetricType.CONTINUOUS, {'method': 'minmax'})
    
    # Calculate weighted scores
    metrics = list(weights.keys())
    scores = weighting_engine.calculate_weighted_score(
        df, campaign_id, metrics, strategy=WeightingStrategy.LINEAR
    )
    
    logger.info(f"Weighted scores calculated for {len(scores)} records")
    logger.info(f"Score range: {scores.min():.2f} - {scores.max():.2f}")
    logger.info(f"Average score: {scores.mean():.2f}")
    
    # Validate weights
    validation = weighting_engine.validate_weights(campaign_id)
    logger.info(f"Weight validation: {validation['valid']}")
    
    return weighting_engine, scores

def demonstrate_explanation():
    """Demonstrate score explanation"""
    logger.info("\n=== Score Explanation Demo ===")
    
    df = create_sample_data()
    
    # Create sample scores
    np.random.seed(42)
    scores = pd.Series(np.random.normal(70, 15, len(df)))
    
    # Initialize explainer
    explainer = ScoreExplainer()  # No OpenAI key for demo
    
    # Configure explanation
    config = ExplanationConfig(
        explanation_type=ExplanationType.SCORE_BREAKDOWN,
        include_metrics=['revenue', 'profit_margin', 'growth_rate', 'market_share', 'customer_satisfaction']
    )
    
    # Generate explanation
    explanation = explainer.generate_score_explanation(df, scores, config)
    
    logger.info(f"Explanation generated: {explanation['explanation_type']}")
    logger.info(f"Total records analyzed: {explanation['metadata']['total_records']}")
    logger.info(f"Recommendations: {len(explanation['recommendations'])}")
    
    # Export explanation
    text_explanation = explainer.export_explanation(explanation, format='text')
    logger.info("Text explanation generated")
    
    return explainer, explanation

def demonstrate_full_scoring_engine():
    """Demonstrate the complete scoring engine"""
    logger.info("\n=== Complete Scoring Engine Demo ===")
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize scoring engine
    engine = ScoringEngine()  # No OpenAI key for demo
    
    # Configure scoring process
    config = {
        'outlier_config': {
            'method': OutlierMethod.IQR,
            'action': OutlierAction.MARK
        },
        'normalization_config': {
            'method': 'zscore',
            'columns': ['revenue', 'profit_margin', 'growth_rate', 'market_share', 'customer_satisfaction']
        },
        'weighting_config': {
            'strategy': WeightingStrategy.LINEAR,
            'metrics': ['revenue', 'profit_margin', 'growth_rate', 'market_share', 'customer_satisfaction']
        }
    }
    
    # Run complete scoring process
    campaign_id = 1
    results = engine.calculate_scores(df, campaign_id, config)
    
    logger.info("Complete scoring process finished!")
    logger.info(f"Results summary:")
    logger.info(f"  - Total records: {results['metadata']['total_records']}")
    logger.info(f"  - Average score: {results['metadata']['average_score']:.2f}")
    logger.info(f"  - Score range: {results['metadata']['score_range']}")
    logger.info(f"  - Processing time: {results['metadata']['processing_time']:.2f}s")
    
    # Show explanation summary
    explanation = results['explanation']
    logger.info(f"  - Explanation type: {explanation['explanation_type']}")
    logger.info(f"  - Recommendations: {len(explanation['recommendations'])}")
    
    # Show outlier summary
    outlier_summary = results['outlier_summary']
    logger.info(f"  - Outliers detected: {sum(outlier_summary['outlier_counts'].values())}")
    
    return engine, results

def demonstrate_method_comparison():
    """Demonstrate comparing different scoring methods"""
    logger.info("\n=== Method Comparison Demo ===")
    
    df = create_sample_data()
    engine = ScoringEngine()
    
    # Define different scoring configurations
    methods = [
        {
            'outlier_config': {'method': OutlierMethod.IQR, 'action': OutlierAction.MARK},
            'normalization_config': {'method': 'zscore'},
            'weighting_config': {'strategy': WeightingStrategy.LINEAR}
        },
        {
            'outlier_config': {'method': OutlierMethod.ZSCORE, 'action': OutlierAction.CAP},
            'normalization_config': {'method': 'minmax'},
            'weighting_config': {'strategy': WeightingStrategy.EXPONENTIAL}
        },
        {
            'outlier_config': {'method': OutlierMethod.ISOLATION_FOREST, 'action': OutlierAction.REMOVE},
            'normalization_config': {'method': 'robust'},
            'weighting_config': {'strategy': WeightingStrategy.LOGARITHMIC}
        }
    ]
    
    # Compare methods
    comparison = engine.compare_scoring_methods(df, 1, methods)
    
    logger.info("Method comparison results:")
    for method_name, result in comparison.items():
        if 'error' not in result:
            logger.info(f"  {method_name}:")
            logger.info(f"    - Average score: {result['average_score']:.2f}")
            logger.info(f"    - Score range: {result['score_range']}")
            logger.info(f"    - Processing time: {result['processing_time']:.2f}s")
        else:
            logger.info(f"  {method_name}: Error - {result['error']}")
    
    return comparison

def main():
    """Run all demonstrations"""
    logger.info("Starting Scoring Engine Demonstrations")
    logger.info("=" * 50)
    
    try:
        # Run individual component demonstrations
        processed_df = demonstrate_preprocessing()
        normalizer = demonstrate_normalization()
        detector, handled_df = demonstrate_outlier_detection()
        weighting_engine, scores = demonstrate_weighting()
        explainer, explanation = demonstrate_explanation()
        
        # Run complete scoring engine demonstration
        engine, results = demonstrate_full_scoring_engine()
        
        # Run method comparison
        comparison = demonstrate_method_comparison()
        
        logger.info("\n" + "=" * 50)
        logger.info("All demonstrations completed successfully!")
        logger.info("The scoring engine is ready for production use.")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        raise

if __name__ == "__main__":
    main() 