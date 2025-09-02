"""
Results processor implementing document requirements for results page
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class ResultsProcessor:
    """Processes scoring results according to document specifications"""
    
    def __init__(self):
        self.whitelist_threshold = 0.75  # Top 25%
        self.blacklist_threshold = 0.25  # Bottom 25%
    
    def process_scoring_results(self, df: pd.DataFrame, source: str, channel: str, 
                              goal: str, ctr_sensitive: bool = False, 
                              analysis_level: str = 'Domain-level', 
                              original_data: pd.DataFrame = None) -> Dict:
        """
        Process complete scoring results according to document requirements
        
        Args:
            df: DataFrame with scores (normalized)
            source: Data source
            channel: Channel type
            goal: Campaign goal
            ctr_sensitive: Whether CTR sensitivity applies
            analysis_level: Analysis level
            original_data: Original data before normalization (for standard format)
            
        Returns:
            Complete results summary
        """
        logger.info(f"Processing scoring results for {source} {channel} {goal}")
        
        # Ensure required columns exist
        if 'score' not in df.columns:
            raise ValueError("DataFrame must contain 'score' column")
        
        # Calculate campaign summary
        campaign_summary = self._calculate_campaign_summary(df, source, channel, goal, ctr_sensitive)
        
        # Get top and bottom performers
        top_performers, bottom_performers = self._get_performance_extremes(df)
        
        # Generate SSP guidance if applicable
        ssp_guidance = self._generate_ssp_guidance(df, source, channel)
        
        # Create optimization lists
        whitelist, blacklist = self._create_optimization_lists(df, source)
        
        # Prepare results table
        results_table = self._prepare_results_table(df, source, channel)
        
        # Generate standard scoring results in requested format
        # Use original data for metrics, but scored data for scores
        if original_data is not None:
            standard_results = self.generate_standard_scoring_results(original_data, df, source, channel)
            standard_summary = self._create_standard_summary_from_results(standard_results)
        else:
            standard_results = self.generate_standard_scoring_results(df, df, source, channel)
            standard_summary = self._create_standard_summary_from_results(standard_results)
        
        # Compile complete results
        complete_results = {
            'campaign_summary': campaign_summary,
            'performance_extremes': {
                'top_5': top_performers,
                'bottom_5': bottom_performers
            },
            'ssp_guidance': ssp_guidance,
            'optimization_lists': {
                'whitelist': whitelist,
                'blacklist': blacklist
            },
            'results_table': results_table,
            'standard_scoring_results': standard_results,  # New: Standard format
            'standard_scoring_summary': standard_summary,  # New: Summary of standard format
            'export_data': self._prepare_export_data(df, source, channel),
            'metadata': {
                'source': source,
                'channel': channel,
                'goal': goal,
                'ctr_sensitive': ctr_sensitive,
                'analysis_level': analysis_level,
                'total_rows': len(df),
                'scored_rows': len(df[df['score'].notna()])
            }
        }
        
        logger.info(f"Results processing completed: {len(df)} rows processed")
        return complete_results
    
    def _calculate_campaign_summary(self, df: pd.DataFrame, source: str, channel: str, 
                                  goal: str, ctr_sensitive: bool) -> Dict:
        """Calculate campaign summary using Grand Total row logic"""
        summary = {
            'overall_score': None,
            'average_score': float(df['score'].mean()) if 'score' in df.columns else 0.0,
            'score_distribution': {},
            'campaign_metrics': {}
        }
        
        # Calculate overall score (separately from row-level exclusions)
        if 'score' in df.columns:
            scores = df['score'].dropna()
            if len(scores) > 0:
                summary['overall_score'] = float(scores.mean())
                summary['score_distribution'] = {
                    'min': float(scores.min()),
                    'max': float(scores.max()),
                    'mean': float(scores.mean()),
                    'median': float(scores.median()),
                    'std': float(scores.std()),
                    'q25': float(scores.quantile(0.25)),
                    'q75': float(scores.quantile(0.75))
                }
        
        # Add source/channel specific metrics
        if source == 'TTD':
            if channel == 'display':
                summary['campaign_metrics'] = {
                    'total_impressions': int(df['impressions'].sum()) if 'impressions' in df.columns else 0,
                    'total_cost': float(df['advertiser_cost'].sum()) if 'advertiser_cost' in df.columns else 0.0,
                    'average_cpm': float(df['cpm'].mean()) if 'cpm' in df.columns else 0.0,
                    'average_ctr': float(df['ctr'].mean()) if 'ctr' in df.columns else 0.0
                }
            elif channel == 'ctv':
                summary['campaign_metrics'] = {
                    'total_impressions': int(df['impressions'].sum()) if 'impressions' in df.columns else 0,
                    'total_cost': float(df['advertiser_cost'].sum()) if 'advertiser_cost' in df.columns else 0.0,
                    'unique_supply_vendors': int(df['supply_vendor'].nunique()) if 'supply_vendor' in df.columns else 0
                }
        
        elif source == 'PulsePoint':
            summary['campaign_metrics'] = {
                'total_impressions': int(df['impressions'].sum()) if 'impressions' in df.columns else 0,
                'total_spend': float(df['total_spend'].sum()) if 'total_spend' in df.columns else 0.0,
                'unique_domains': int(df['domain'].nunique()) if 'domain' in df.columns else 0,
                'average_ecpm': float(df['ecpm'].mean()) if 'ecpm' in df.columns else 0.0
            }
        
        return summary
    
    def _get_performance_extremes(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """Get top 5 and bottom 5 performers"""
        if 'score' not in df.columns:
            return [], []
        
        # Get top 5 performers
        top_5 = df.nlargest(5, 'score')
        top_performers = []
        
        for _, row in top_5.iterrows():
            performer = {
                'name': self._get_identifier(row),
                'score': float(row['score']),
                'impressions': int(row.get('impressions', 0)),
                'status': row.get('status', 'Unknown')
            }
            top_performers.append(performer)
        
        # Get bottom 5 performers
        bottom_5 = df.nsmallest(5, 'score')
        bottom_performers = []
        
        for _, row in bottom_5.iterrows():
            performer = {
                'name': self._get_identifier(row),
                'score': float(row['score']),
                'impressions': int(row.get('impressions', 0)),
                'status': row.get('status', 'Unknown')
            }
            bottom_performers.append(performer)
        
        return top_performers, bottom_performers
    
    def _get_identifier(self, row: pd.Series) -> str:
        """Get identifier for the row (domain, site, or supply vendor)"""
        # Check for both lowercase (processed) and uppercase (original) column names
        if 'domain' in row:
            return str(row['domain'])
        elif 'Domain' in row:
            return str(row['Domain'])
        elif 'site' in row:
            return str(row['site'])
        elif 'Site' in row:
            return str(row['Site'])
        elif 'supply_vendor' in row:
            return str(row['supply_vendor'])
        elif 'Supply Vendor' in row:
            return str(row['Supply Vendor'])
        else:
            return 'Unknown'
    
    def _generate_ssp_guidance(self, df: pd.DataFrame, source: str, channel: str) -> Dict:
        """Generate SSP guidance if unique supply vendors > 10"""
        ssp_guidance = {
            'show_guidance': False,
            'benchmark_ssps': [],
            'total_ssps': 0
        }
        
        if source == 'TTD' and 'supply_vendor' in df.columns:
            unique_ssps = df['supply_vendor'].nunique()
            ssp_guidance['total_ssps'] = unique_ssps
            
            if unique_ssps > 10:
                ssp_guidance['show_guidance'] = True
                
                # Get benchmark SSPs (5-7 as per document)
                benchmark_count = min(7, max(5, unique_ssps // 3))
                
                # Calculate average score per SSP
                ssp_scores = df.groupby('supply_vendor')['score'].agg(['mean', 'count']).reset_index()
                ssp_scores = ssp_scores[ssp_scores['count'] >= 5]  # Minimum 5 impressions
                
                if len(ssp_scores) > 0:
                    # Sort by score and get top performers
                    benchmark_ssps = ssp_scores.nlargest(benchmark_count, 'mean')
                    
                    for _, ssp in benchmark_ssps.iterrows():
                        ssp_guidance['benchmark_ssps'].append({
                            'name': str(ssp['supply_vendor']),
                            'average_score': float(ssp['mean']),
                            'impression_count': int(ssp['count'])
                        })
        
        return ssp_guidance
    
    def _create_optimization_lists(self, df: pd.DataFrame, source: str) -> Tuple[List[str], List[str]]:
        """Create whitelist and blacklist based on document requirements"""
        if 'score' not in df.columns:
            return [], []
        
        # Apply minimum thresholds
        if source == 'PulsePoint':
            # Require ≥ 0.05% of total impressions
            total_impressions = df['impressions'].sum()
            min_impressions = total_impressions * 0.0005
            df_filtered = df[df['impressions'] >= min_impressions]
        elif source == 'TTD':
            # Require ≥ 250 impressions
            df_filtered = df[df['impressions'] >= 250]
        else:
            df_filtered = df
        
        if len(df_filtered) == 0:
            return [], []
        
        # Calculate percentiles
        scores = df_filtered['score'].dropna()
        if len(scores) == 0:
            return [], []
        
        whitelist_threshold = scores.quantile(self.whitelist_threshold)
        blacklist_threshold = scores.quantile(self.blacklist_threshold)
        
        # Create whitelist (top 25%)
        whitelist_df = df_filtered[df_filtered['score'] >= whitelist_threshold]
        whitelist = [self._get_identifier(row) for _, row in whitelist_df.iterrows()]
        
        # Create blacklist (bottom 25%)
        blacklist_df = df_filtered[df_filtered['score'] <= blacklist_threshold]
        blacklist = [self._get_identifier(row) for _, row in blacklist_df.iterrows()]
        
        # Remove [tail aggregate] from both lists
        whitelist = [item for item in whitelist if '[tail aggregate]' not in str(item)]
        blacklist = [item for item in blacklist if '[tail aggregate]' not in str(item)]
        
        logger.info(f"Created optimization lists: {len(whitelist)} whitelist, {len(blacklist)} blacklist")
        return whitelist, blacklist
    
    def _prepare_results_table(self, df: pd.DataFrame, source: str, channel: str) -> List[Dict]:
        """Prepare results table with original IDs + metrics + scores"""
        results_table = []
        
        for _, row in df.iterrows():
            result_row = {
                'identifier': self._get_identifier(row),
                'score': float(row['score']) if 'score' in row else 0.0,
                'status': row.get('status', 'Unknown'),
                'impressions': int(row.get('impressions', 0)),
                'original_metrics': {}
            }
            
            # Add original metrics based on source/channel
            if source == 'TTD':
                if channel == 'display':
                    result_row['original_metrics'] = {
                        'site': str(row.get('site', '')),
                        'supply_vendor': str(row.get('supply_vendor', '')),
                        'advertiser_cost': float(row.get('advertiser_cost', 0)),
                        'cpm': float(row.get('cpm', 0)),
                        'ctr': float(row.get('ctr', 0)),
                        'ias_display_fully_in_view_1s': float(row.get('ias_display_fully_in_view_1s', 0)),
                        'ad_load_rate': float(row.get('ad_load_rate', 0)),
                        'ad_refresh_rate': float(row.get('ad_refresh_rate', 0))
                    }
                elif channel == 'ctv':
                    result_row['original_metrics'] = {
                        'supply_vendor': str(row.get('supply_vendor', '')),
                        'advertiser_cost': float(row.get('advertiser_cost', 0)),
                        'impressions': int(row.get('impressions', 0)),
                        'tv_quality_index_ratio': float(row.get('tv_quality_index_ratio', 0)),
                        'unique_id_ratio': float(row.get('unique_id_ratio', 0))
                    }
            
            elif source == 'PulsePoint':
                result_row['original_metrics'] = {
                    'domain': str(row.get('domain', '')),
                    'total_spend': float(row.get('total_spend', 0)),
                    'impressions': int(row.get('impressions', 0)),
                    'ecpm': float(row.get('ecpm', 0)),
                    'ctr': float(row.get('ctr', 0)),
                    'conversions': int(row.get('conversions', 0))
                }
                
                if channel == 'video':
                    result_row['original_metrics']['completion_rate'] = float(row.get('completion_rate', 0))
            
            results_table.append(result_row)
        
        return results_table
    
    def _prepare_export_data(self, df: pd.DataFrame, source: str, channel: str) -> Dict:
        """Prepare data for exports (XLSX/CSV, Whitelist, Blacklist)"""
        export_data = {
            'scored_file_columns': [],
            'whitelist_columns': [],
            'blacklist_columns': []
        }
        
        # Define columns for scored file export
        base_columns = ['score', 'status', 'impressions']
        
        if source == 'TTD':
            if channel == 'display':
                export_data['scored_file_columns'] = base_columns + [
                    'site', 'supply_vendor', 'advertiser_cost', 'cpm', 'ctr',
                    'ias_display_fully_in_view_1s', 'ad_load_rate', 'ad_refresh_rate'
                ]
            elif channel == 'ctv':
                export_data['scored_file_columns'] = base_columns + [
                    'supply_vendor', 'advertiser_cost', 'tv_quality_index_ratio', 'unique_id_ratio'
                ]
        
        elif source == 'PulsePoint':
            export_data['scored_file_columns'] = base_columns + [
                'domain', 'total_spend', 'ecpm', 'ctr', 'conversions'
            ]
            
            if channel == 'video':
                export_data['scored_file_columns'].append('completion_rate')
        
        # Columns for optimization lists
        export_data['whitelist_columns'] = ['identifier', 'score', 'impressions']
        export_data['blacklist_columns'] = ['identifier', 'score', 'impressions']
        
        return export_data

    def generate_standard_scoring_results(self, original_df: pd.DataFrame, scored_df: pd.DataFrame, source: str, channel: str) -> List[Dict]:
        """
        Generate standard scoring results in the exact format requested:
        Domain, Publisher, CPM, CTR, Conv Rate, Score (0-100)
        
        Args:
            original_df: DataFrame with original metrics (CPM, CTR, etc.)
            scored_df: DataFrame with scores and rankings
            source: Data source (TTD, PulsePoint)
            channel: Channel type (Display, Video, Audio, CTV)
        """
        standard_results = []
        
        # Create a mapping between original and scored data
        # We'll use the identifier to match rows
        for _, scored_row in scored_df.iterrows():
            # Get the identifier from scored data
            identifier = self._get_identifier(scored_row)
            
            # Find the corresponding row in original data
            original_row = None
            for _, orig_row in original_df.iterrows():
                orig_identifier = self._get_identifier(orig_row)
                if orig_identifier == identifier:
                    original_row = orig_row
                    break
            
            if original_row is None:
                # If no match found, skip this row
                continue
            
            # Prepare the standard result row
            result_row = {
                'Domain': identifier,
                'Publisher': '',
                'CPM': 0.0,
                'CTR': 0.0,
                'Conv Rate': 0.0,
                'Score': float(scored_row.get('score', 0.0))
            }
            
            # Fill in the metrics based on source and channel
            if source == 'TTD':
                if channel.lower() == 'display':
                    result_row.update({
                        'Publisher': str(original_row.get('Supply Vendor', '')),
                        'CPM': float(original_row.get('CPM', 0.0)),
                        'CTR': float(original_row.get('CTR', 0.0)) * 100,  # Convert to percentage
                        'Conv Rate': float(original_row.get('All Last Click + View Conversion Rate', 0.0)) * 100  # Convert to percentage
                    })
                elif channel == 'ctv':
                    result_row.update({
                        'Publisher': str(original_row.get('Supply Vendor', '')),
                        'CPM': float(original_row.get('Advertiser Cost', 0.0)) / float(original_row.get('Impressions', 1)) * 1000,  # Calculate CPM
                        'CTR': 0.0,  # CTV doesn't have CTR
                        'Conv Rate': 0.0  # CTV doesn't have conversion rate
                    })
                elif channel == 'video':
                    result_row.update({
                        'Publisher': str(original_row.get('Supply Vendor', '')),
                        'CPM': float(original_row.get('Advertiser Cost', 0.0)) / float(original_row.get('Impressions', 1)) * 1000,  # Calculate CPM
                        'CTR': float(original_row.get('CTR', 0.0)) * 100,  # Convert to percentage
                        'Conv Rate': float(original_row.get('Completion Rate', 0.0)) * 100  # Use completion rate as conversion
                    })
                elif channel == 'audio':
                    result_row.update({
                        'Publisher': str(original_row.get('Supply Vendor', '')),
                        'CPM': float(original_row.get('Advertiser Cost', 0.0)) / float(original_row.get('Impressions', 1)) * 1000,  # Calculate CPM
                        'CTR': float(original_row.get('CTR', 0.0)) * 100,  # Convert to percentage
                        'Conv Rate': float(original_row.get('Completion Rate', 0.0)) * 100  # Use completion rate as conversion
                    })
            
            elif source == 'PulsePoint':
                result_row.update({
                    'Publisher': str(original_row.get('Publisher', '')),
                    'CPM': float(original_row.get('eCPM', 0.0)),  # PulsePoint uses eCPM
                    'CTR': float(original_row.get('CTR', 0.0)) * 100,  # Convert to percentage
                    'Conv Rate': float(original_row.get('Conversions', 0.0)) / float(original_row.get('Impressions', 1)) * 100  # Calculate conversion rate
                })
            
            standard_results.append(result_row)
        
        return standard_results

    def get_standard_scoring_summary(self, original_df: pd.DataFrame, scored_df: pd.DataFrame, source: str, channel: str) -> Dict:
        """
        Get a summary of the standard scoring results
        """
        standard_results = self.generate_standard_scoring_results(original_df, scored_df, source, channel)
        
        if not standard_results:
            return {}
        
        # Calculate summary statistics
        scores = [row['Score'] for row in standard_results]
        cpm_values = [row['CPM'] for row in standard_results if row['CPM'] > 0]
        ctr_values = [row['CTR'] for row in standard_results if row['CTR'] > 0]
        conv_rates = [row['Conv Rate'] for row in standard_results if row['Conv Rate'] > 0]
        
        summary = {
            'total_domains': len(standard_results),
            'score_summary': {
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0,
                'average': sum(scores) / len(scores) if scores else 0,
                'median': sorted(scores)[len(scores)//2] if scores else 0
            },
            'cpm_summary': {
                'min': min(cpm_values) if cpm_values else 0,
                'max': max(cpm_values) if cpm_values else 0,
                'average': sum(cpm_values) / len(cpm_values) if cpm_values else 0
            },
            'ctr_summary': {
                'min': min(ctr_values) if ctr_values else 0,
                'max': max(ctr_values) if ctr_values else 0,
                'average': sum(ctr_values) / len(ctr_values) if ctr_values else 0
            },
            'conversion_summary': {
                'min': min(conv_rates) if conv_rates else 0,
                'max': max(conv_rates) if conv_rates else 0,
                'average': sum(conv_rates) / len(conv_rates) if conv_rates else 0
            }
        }
        
        return summary

    def _create_standard_summary_from_results(self, standard_results: List[Dict]) -> Dict:
        """
        Create a summary from existing standard scoring results without regenerating them
        
        Args:
            standard_results: List of standard scoring result dictionaries
            
        Returns:
            Summary dictionary
        """
        if not standard_results:
            return {}
        
        # Calculate summary statistics
        scores = [row['Score'] for row in standard_results]
        cpm_values = [row['CPM'] for row in standard_results if row['CPM'] > 0]
        ctr_values = [row['CTR'] for row in standard_results if row['CTR'] > 0]
        conv_rates = [row['Conv Rate'] for row in standard_results if row['Conv Rate'] > 0]
        
        summary = {
            'total_domains': len(standard_results),
            'score_summary': {
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0,
                'average': sum(scores) / len(scores) if scores else 0,
                'median': sorted(scores)[len(scores)//2] if scores else 0
            },
            'cpm_summary': {
                'min': min(cpm_values) if cpm_values else 0,
                'max': max(cpm_values) if cpm_values else 0,
                'average': sum(cpm_values) / len(cpm_values) if cpm_values else 0
            },
            'ctr_summary': {
                'min': min(ctr_values) if ctr_values else 0,
                'max': max(ctr_values) if ctr_values else 0,
                'average': sum(ctr_values) / len(ctr_values) if ctr_values else 0
            },
            'conversion_summary': {
                'min': min(conv_rates) if conv_rates else 0,
                'max': max(conv_rates) if conv_rates else 0,
                'average': sum(conv_rates) / len(conv_rates) if conv_rates else 0
            }
        }
        
        return summary
