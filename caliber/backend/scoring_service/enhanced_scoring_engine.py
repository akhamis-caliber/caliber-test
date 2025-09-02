"""
Enhanced Scoring Engine implementing complete document requirements
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
import logging

from .source_detector import SourceDetector
from .enhanced_preprocess import EnhancedPreprocessor
from .enhanced_normalize import EnhancedNormalizer
from .enhanced_weighting import EnhancedWeighting
from .results_processor import ResultsProcessor
from .scoring import calculate_domain_scores, rank_domains

logger = logging.getLogger(__name__)


class EnhancedScoringEngine:
    """
    Complete scoring engine implementing document specifications for:
    - Source detection (PulsePoint vs TTD)
    - Campaign controls (Goal, Channel, CTR-sensitive)
    - Required input validation
    - Enhanced preprocessing
    - Proper normalization with metric directions
    - Document-specific scoring models
    - Complete results processing
    """
    
    def __init__(self):
        self.source_detector = SourceDetector()
        self.preprocessor = EnhancedPreprocessor()
        self.normalizer = EnhancedNormalizer()
        self.weighting = EnhancedWeighting()
        self.results_processor = ResultsProcessor()
    
    def score_campaign_data(self, df: pd.DataFrame, campaign_config: Dict) -> Dict:
        """
        Complete scoring pipeline for campaign data
        
        Args:
            df: Input DataFrame with campaign data
            campaign_config: Campaign configuration including:
                - goal: 'Awareness' or 'Action'
                - channel: 'Display', 'Video', 'Audio', 'CTV'
                - ctr_sensitive: boolean (for TTD Display Awareness)
                - analysis_level: 'Domain-level' or 'Supply Vendor-level'
                - file_name: Optional file name for results
        
        Returns:
            Complete scoring results and analysis
        """
        logger.info("Starting enhanced scoring engine")
        
        try:
            # Step 1: Auto-detect data source
            source, channel, detection_summary = self.source_detector.detect_source(df)
            
            if source == 'Unknown':
                raise ValueError(f"Could not determine data source. Available columns: {list(df.columns)}")
            
            # Override channel if specified in config
            if 'channel' in campaign_config:
                channel = campaign_config['channel']
            
            # Step 2: Validate required inputs
            goal = campaign_config.get('goal', 'Awareness')
            ctr_sensitive = campaign_config.get('ctr_sensitive', False)
            analysis_level = campaign_config.get('analysis_level', 'Domain-level')
            
            is_valid, missing_fields = self.source_detector.validate_required_inputs(
                df, source, channel, goal, ctr_sensitive
            )
            
            if not is_valid:
                raise ValueError(f"Missing required fields for {source} {channel} {goal}: {missing_fields}")
            
            # Step 3: Enhanced preprocessing
            df_processed, preprocessing_summary = self.preprocessor.preprocess_for_scoring(
                df, source, channel, analysis_level
            )
            
            if len(df_processed) == 0:
                raise ValueError("No data remaining after preprocessing")
            
            # Step 4: Enhanced normalization
            df_normalized, normalization_summary = self.normalizer.normalize_campaign_metrics(
                df_processed, source, channel, goal, ctr_sensitive
            )
            
            # Step 5: Get scoring model and weights
            weights = self.weighting.get_scoring_model(source, channel, goal, ctr_sensitive)
            metric_mapping = self.weighting.get_metric_mapping(source, channel)
            
            # Step 6: Calculate scores
            feature_columns = normalization_summary['feature_columns']
            df_scored, scoring_summary = calculate_domain_scores(
                df_normalized, weights, feature_columns
            )
            
            # Step 7: Add ranking
            df_ranked, ranking_summary = rank_domains(df_scored)
            
            # Step 8: Process results
            # Pass both original and processed data for complete results
            results = self.results_processor.process_scoring_results(
                df_ranked, source, channel, goal, ctr_sensitive, analysis_level, 
                original_data=df  # Pass truly original data with original column names
            )
            
            # Step 9: Compile complete summary
            complete_summary = {
                'source_detection': {
                    'detected_source': source,
                    'detected_channel': channel,
                    'detection_summary': detection_summary
                },
                'campaign_config': {
                    'goal': goal,
                    'channel': channel,
                    'ctr_sensitive': ctr_sensitive,
                    'analysis_level': analysis_level,
                    'file_name': campaign_config.get('file_name', 'Unknown')
                },
                'preprocessing': preprocessing_summary,
                'normalization': normalization_summary,
                'scoring': {
                    'weights_used': weights,
                    'metric_mapping': metric_mapping,
                    'scoring_summary': scoring_summary,
                    'ranking_summary': ranking_summary
                },
                'results': results,
                'scoring_model_info': self.weighting.get_scoring_summary(source, channel, goal, ctr_sensitive)
            }
            
            logger.info(f"Enhanced scoring completed successfully for {source} {channel} {goal}")
            return complete_summary
            
        except Exception as e:
            logger.error(f"Error in enhanced scoring engine: {str(e)}")
            raise
    
    def get_available_configurations(self, df: pd.DataFrame) -> Dict:
        """
        Get available campaign configurations based on detected source
        
        Args:
            df: Input DataFrame
            
        Returns:
            Available configurations
        """
        source, channel, _ = self.source_detector.detect_source(df)
        
        if source == 'Unknown':
            return {'error': 'Could not determine data source'}
        
        configurations = {
            'source': source,
            'detected_channel': channel,
            'available_goals': ['Awareness', 'Action'],
            'available_channels': self._get_available_channels(source),
            'analysis_levels': self.source_detector.get_analysis_level_options(source, channel),
            'ctr_sensitive_applicable': source == 'TTD' and channel == 'display'
        }
        
        return configurations
    
    def _get_available_channels(self, source: str) -> List[str]:
        """Get available channels for the source"""
        if source == 'TTD':
            return ['Display', 'Video', 'Audio', 'CTV']
        elif source == 'PulsePoint':
            return ['Display', 'Video']
        else:
            return ['Display']
    
    def validate_campaign_config(self, df: pd.DataFrame, campaign_config: Dict) -> Tuple[bool, List[str]]:
        """
        Validate campaign configuration against available data
        
        Args:
            df: Input DataFrame
            campaign_config: Campaign configuration
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        errors = []
        
        # Detect source first
        source, channel, _ = self.source_detector.detect_source(df)
        
        if source == 'Unknown':
            errors.append("Could not determine data source")
            return False, errors
        
        # Validate goal
        goal = campaign_config.get('goal')
        if goal not in ['Awareness', 'Action']:
            errors.append(f"Invalid goal: {goal}. Must be 'Awareness' or 'Action'")
        
        # Validate channel
        config_channel = campaign_config.get('channel')
        if config_channel:
            available_channels = self._get_available_channels(source)
            if config_channel not in available_channels:
                errors.append(f"Invalid channel '{config_channel}' for {source}. Available: {available_channels}")
        
        # Validate CTR sensitivity
        ctr_sensitive = campaign_config.get('ctr_sensitive', False)
        if ctr_sensitive and not (source == 'TTD' and channel == 'display'):
            errors.append("CTR sensitivity only applies to TTD Display campaigns")
        
        # Validate analysis level
        analysis_level = campaign_config.get('analysis_level')
        if analysis_level:
            available_levels = self.source_detector.get_analysis_level_options(source, channel)
            if analysis_level not in available_levels:
                errors.append(f"Invalid analysis level '{analysis_level}' for {source} {channel}. Available: {available_levels}")
        
        # Validate required inputs
        if goal:
            is_valid, missing_fields = self.source_detector.validate_required_inputs(
                df, source, channel, goal, ctr_sensitive
            )
            if not is_valid:
                errors.append(f"Missing required fields: {missing_fields}")
        
        return len(errors) == 0, errors
    
    def get_scoring_preview(self, df: pd.DataFrame, campaign_config: Dict) -> Dict:
        """
        Get preview of scoring configuration without running full scoring
        
        Args:
            df: Input DataFrame
            campaign_config: Campaign configuration
            
        Returns:
            Scoring preview information
        """
        try:
            source, channel, _ = self.source_detector.detect_source(df)
            
            if source == 'Unknown':
                return {'error': 'Could not determine data source'}
            
            goal = campaign_config.get('goal', 'Awareness')
            ctr_sensitive = campaign_config.get('ctr_sensitive', False)
            
            # Get scoring model preview
            scoring_summary = self.weighting.get_scoring_summary(source, channel, goal, ctr_sensitive)
            
            # Get available metrics
            available_metrics = self.normalizer._get_metrics_for_normalization(
                source, channel, goal, ctr_sensitive
            )
            
            preview = {
                'source': source,
                'channel': channel,
                'goal': goal,
                'ctr_sensitive': ctr_sensitive,
                'scoring_model': scoring_summary,
                'available_metrics': available_metrics,
                'metric_directions': self.normalizer._get_metric_directions(available_metrics),
                'data_preview': {
                    'total_rows': len(df),
                    'columns': list(df.columns),
                    'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                }
            }
            
            return preview
            
        except Exception as e:
            logger.error(f"Error generating scoring preview: {str(e)}")
            return {'error': str(e)}
    
    def export_results(self, results: Dict, export_format: str = 'json') -> str:
        """
        Export results in specified format
        
        Args:
            results: Complete scoring results
            export_format: Export format ('json', 'csv', 'xlsx')
            
        Returns:
            Export file path or data
        """
        if export_format == 'json':
            return results
        
        elif export_format == 'csv':
            # Export main results table
            results_table = results['results']['results_table']
            if results_table:
                df_export = pd.DataFrame(results_table)
                return df_export.to_csv(index=False)
        
        elif export_format == 'xlsx':
            # Export multiple sheets
            # This would require openpyxl or xlsxwriter
            logger.warning("XLSX export not implemented yet")
            return "XLSX export not implemented"
        
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
