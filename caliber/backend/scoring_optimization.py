#!/usr/bin/env python3
"""
Scoring Optimization Module
Implements performance optimizations for faster scoring processing with progress tracking
"""

import asyncio
import logging
import pandas as pd
import io
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from scoring_integration import ScoringIntegration
import redis.asyncio as redis

# Import progress tracking and performance monitoring
try:
    from websocket_progress import progress_manager
    from performance_monitor import performance_monitor, MetricType, track_performance
    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False
    logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class OptimizedScoringProcessor:
    """
    Optimized scoring processor with:
    - Async processing
    - Batch database operations
    - Caching (with fallback)
    - Parallel processing
    - Timeout protection
    - Progress tracking
    - Performance monitoring
    """
    
    def __init__(self):
        self.scoring_integration = ScoringIntegration()
        self.redis_client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.progress_available = PROGRESS_AVAILABLE
        
    async def initialize_redis(self):
        """Initialize Redis connection for caching with fallback"""
        try:
            # Try multiple Redis connection options
            redis_hosts = [
                'caliber-redis-1',  # Docker service name
                'localhost',         # Local development
                '127.0.0.1',        # Local development
                'redis'             # Generic Redis service name
            ]
            
            for host in redis_hosts:
                try:
                    logger.info(f"Attempting Redis connection to {host}:6379")
                    self.redis_client = redis.Redis(
                        host=host,
                        port=6379,
                        decode_responses=True,
                        socket_connect_timeout=2.0,  # 2 second timeout
                        socket_timeout=5.0,          # 5 second operation timeout
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                    await self.redis_client.ping()
                    logger.info(f"✅ Redis connection established to {host}:6379")
                    return
                except Exception as e:
                    logger.debug(f"Redis connection to {host} failed: {e}")
                    continue
            
            # If all Redis connections fail, disable caching
            logger.warning("All Redis connections failed, caching disabled")
            self.redis_client = None
            
        except Exception as e:
            logger.warning(f"Redis initialization failed, caching disabled: {e}")
            self.redis_client = None
    
    @track_performance(MetricType.PROCESSING_TIME)
    async def process_file_optimized(
        self, 
        file_content: bytes, 
        filename: str, 
        report_id: str, 
        campaign_config: Dict,
        campaign_id: str = None
    ) -> Dict[str, Any]:
        """
        Optimized file processing with async operations, caching, timeout protection, and progress tracking
        """
        start_time = time.time()
        
        # Initialize progress tracking if available
        if self.progress_available and campaign_id:
            try:
                # Estimate total rows from file size
                estimated_rows = len(file_content) // 100  # Rough estimate
                await progress_manager.initialize_progress(
                    campaign_id, filename, estimated_rows
                )
                await progress_manager.update_progress(
                    campaign_id, 'File Processing', 0, 'Initializing scoring process', 5
                )
            except Exception as e:
                logger.warning(f"Progress tracking initialization failed: {e}")
        
        try:
            # Set overall timeout for the entire process (30 seconds)
            async with asyncio.timeout(30.0):
                # Step 1: Check cache for similar files (with timeout)
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'Cache Check', 0, 'Checking for cached results', 10
                    )
                
                cache_key = await self._generate_cache_key(file_content, campaign_config)
                cached_results = await self._get_cached_results(cache_key)
                
                if cached_results:
                    logger.info(f"🚀 Cache hit! Using cached results for {filename}")
                    
                    if self.progress_available and campaign_id:
                        await progress_manager.update_progress(
                            campaign_id, 'Cache Hit', estimated_rows, 'Using cached results', 90
                        )
                    
                    # Convert cached results to data format (not database objects)
                    score_data = await self._convert_cached_to_data_format(
                        cached_results, report_id, campaign_config
                    )
                    processing_time = time.time() - start_time
                    logger.info(f"⚡ Cached processing completed in {processing_time:.2f}s")
                    
                    # Record performance metrics
                    if self.progress_available:
                        await self._record_performance_metrics(
                            campaign_id, filename, len(file_content), len(score_data),
                            processing_time, campaign_config, success=True, cache_hit=True
                        )
                    
                    return {
                        'scores': score_data,
                        'processing_time': processing_time,
                        'cache_hit': True,
                        'total_rows': len(score_data)
                    }
                
                # Step 2: Parse file asynchronously (with timeout)
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'File Parsing', 0, 'Parsing uploaded file', 15
                    )
                
                logger.info(f"🔄 Processing {filename} with optimizations...")
                
                # Parse file in thread pool with timeout
                loop = asyncio.get_event_loop()
                df = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor, 
                        self._parse_file, 
                        file_content, 
                        filename
                    ),
                    timeout=10.0  # 10 second timeout for file parsing
                )
                
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'File Parsed', len(df), 'File parsed successfully', 25
                    )
                
                # Step 3: Run Enhanced Scoring Engine in thread pool (with timeout)
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'Scoring Engine', len(df), 'Running enhanced scoring engine', 40
                    )
                
                enhanced_results = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._run_enhanced_scoring,
                        df,
                        campaign_config
                    ),
                    timeout=15.0  # 15 second timeout for scoring
                )
                
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'Scoring Complete', len(df), 'Enhanced scoring completed', 70
                    )
                
                # Step 4: Batch convert results to data format (not database objects)
                standard_results = enhanced_results.get('results', {}).get('standard_scoring_results', [])
                
                if not standard_results:
                    logger.warning("No standard scoring results generated")
                    if self.progress_available and campaign_id:
                        await progress_manager.complete_progress(campaign_id, success=False, error_message="No scoring results generated")
                    return {'error': 'No scoring results generated'}
                
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'Data Conversion', len(df), 'Converting results to data format', 80
                    )
                
                # Step 5: Convert to data format (not database objects)
                score_data = await self._batch_create_score_data(
                    standard_results, report_id, enhanced_results
                )
                
                # Step 6: Cache results for future use (non-blocking)
                if self.progress_available and campaign_id:
                    await progress_manager.update_progress(
                        campaign_id, 'Caching Results', len(df), 'Caching results for future use', 90
                    )
                
                try:
                    await asyncio.wait_for(
                        self._cache_results(cache_key, enhanced_results),
                        timeout=5.0  # 5 second timeout for caching
                    )
                except asyncio.TimeoutError:
                    logger.warning("Caching timed out, continuing without cache")
                except Exception as e:
                    logger.warning(f"Caching failed: {e}")
                
                processing_time = time.time() - start_time
                logger.info(f"⚡ Optimized processing completed in {processing_time:.2f}s")
                
                # Record performance metrics
                if self.progress_available:
                    await self._record_performance_metrics(
                        campaign_id, filename, len(file_content), len(score_data),
                        processing_time, campaign_config, success=True, cache_hit=False
                    )
                
                # Complete progress tracking
                if self.progress_available and campaign_id:
                    await progress_manager.complete_progress(campaign_id, success=True)
                
                return {
                    'scores': score_data,
                    'processing_time': processing_time,
                    'cache_hit': False,
                    'total_rows': len(score_data),
                    'enhanced_summary': self.scoring_integration.get_enhanced_results_summary(enhanced_results)
                }
                
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            logger.error(f"❌ Scoring timeout after {processing_time:.2f}s")
            
            # Record timeout in performance monitoring
            if self.progress_available and campaign_id:
                await progress_manager.timeout_progress(campaign_id)
                await performance_monitor.record_timeout(campaign_id, filename, processing_time)
            
            raise TimeoutError(f"Scoring process timed out after {processing_time:.2f} seconds")
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in optimized processing: {str(e)}")
            
            # Record error in progress tracking and performance monitoring
            if self.progress_available and campaign_id:
                await progress_manager.complete_progress(campaign_id, success=False, error_message=str(e))
                await self._record_performance_metrics(
                    campaign_id, filename, len(file_content), 0,
                    processing_time, campaign_config, success=False, cache_hit=False
                )
            
            raise

    async def _record_performance_metrics(
        self,
        campaign_id: str,
        filename: str,
        file_size: int,
        total_rows: int,
        processing_time: float,
        campaign_config: Dict,
        success: bool,
        cache_hit: bool
    ):
        """Record performance metrics for monitoring"""
        try:
            await performance_monitor.record_scoring_completion(
                campaign_id=campaign_id,
                filename=filename,
                file_size=file_size,
                total_rows=total_rows,
                processing_time=processing_time,
                source_type=campaign_config.get('source_type', 'unknown'),
                campaign_goal=campaign_config.get('goal', 'unknown'),
                campaign_channel=campaign_config.get('channel', 'unknown'),
                success=success,
                error_message=None if success else "Scoring process failed",
                cache_hit=cache_hit
            )
        except Exception as e:
            logger.warning(f"Failed to record performance metrics: {e}")
    
    def _parse_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse file based on extension"""
        if filename.endswith('.csv'):
            return pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file format")
    
    def _run_enhanced_scoring(self, df: pd.DataFrame, campaign_config: Dict) -> Dict:
        """Run Enhanced Scoring Engine with fallback"""
        try:
            enhanced_config = {
                'goal': campaign_config.get('goal', 'Awareness'),
                'channel': campaign_config.get('channel', 'Display'),
                'ctr_sensitive': campaign_config.get('ctr_sensitive', False),
                'analysis_level': campaign_config.get('analysis_level', 'Domain-level'),
                'file_name': campaign_config.get('file_name', 'Unknown')
            }
            
            return self.scoring_integration.enhanced_engine.score_campaign_data(df, enhanced_config)
            
        except Exception as e:
            logger.warning(f"Enhanced scoring engine failed: {e}, using fallback")
            # For fallback, we'll need to handle this differently since we can't await here
            # We'll return a fallback result directly
            return self._fallback_scoring_sync(df, campaign_config)
    
    async def _fallback_scoring(self, df: pd.DataFrame, campaign_config: Dict) -> Dict:
        """Fallback scoring when enhanced engine fails"""
        try:
            logger.info("🔄 Using fallback scoring mechanism")
            
            # Simple scoring based on basic metrics
            results = []
            for _, row in df.iterrows():
                # Extract basic metrics (handle missing columns gracefully)
                domain = str(row.get('Domain', row.get('domain', 'Unknown')))
                publisher = str(row.get('Publisher', row.get('publisher', 'Unknown')))
                
                # Handle different column names for metrics
                cpm = float(row.get('CPM', row.get('cpm', 0.0)))
                ctr = float(row.get('CTR', row.get('ctr', 0.0)))
                conversion_rate = float(row.get('Conv Rate', row.get('conversion_rate', 0.0)))
                
                # Simple scoring algorithm
                score = 50.0  # Base score
                
                # Adjust based on CPM (lower is better for cost efficiency)
                if cpm > 0:
                    if cpm < 5.0:
                        score += 20
                    elif cpm < 10.0:
                        score += 10
                    elif cpm > 20.0:
                        score -= 10
                
                # Adjust based on CTR (higher is better)
                if ctr > 0:
                    if ctr > 2.0:
                        score += 20
                    elif ctr > 1.0:
                        score += 10
                    elif ctr < 0.5:
                        score -= 10
                
                # Adjust based on conversion rate (higher is better)
                if conversion_rate > 0:
                    if conversion_rate > 5.0:
                        score += 20
                    elif conversion_rate > 2.0:
                        score += 10
                    elif conversion_rate < 1.0:
                        score -= 10
                
                # Clamp score to 0-100 range
                score = max(0, min(100, score))
                
                # Determine status
                if score >= 80:
                    status = 'Good'
                elif score >= 60:
                    status = 'Moderate'
                else:
                    status = 'Poor'
                
                # Create result
                result = {
                    'Domain': domain,
                    'Publisher': publisher,
                    'CPM': cpm,
                    'CTR': ctr,
                    'Conv Rate': conversion_rate,
                    'Score': score,
                    'Status': status
                }
                results.append(result)
            
            logger.info(f"✅ Fallback scoring generated {len(results)} results")
            
            return {
                'results': {
                    'standard_scoring_results': results,
                    'metadata': {
                        'source': 'Fallback',
                        'channel': campaign_config.get('channel', 'Unknown'),
                        'method': 'Basic scoring (enhanced engine failed)'
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback scoring also failed: {e}")
            # Return minimal results to prevent complete failure
            return {
                'results': {
                    'standard_scoring_results': [],
                    'metadata': {
                        'source': 'Error',
                        'channel': 'Unknown',
                        'method': 'Scoring failed completely',
                        'error': str(e)
                    }
                }
            }
    
    def _fallback_scoring_sync(self, df: pd.DataFrame, campaign_config: Dict) -> Dict:
        """Synchronous fallback scoring when enhanced engine fails"""
        try:
            logger.info("🔄 Using synchronous fallback scoring mechanism")
            
            # Simple scoring based on basic metrics
            results = []
            for _, row in df.iterrows():
                # Extract basic metrics (handle missing columns gracefully)
                domain = str(row.get('Domain', row.get('domain', 'Unknown')))
                publisher = str(row.get('Publisher', row.get('publisher', 'Unknown')))
                
                # Handle different column names for metrics
                cpm = float(row.get('CPM', row.get('cpm', 0.0)))
                ctr = float(row.get('CTR', row.get('ctr', 0.0)))
                conversion_rate = float(row.get('Conv Rate', row.get('conversion_rate', 0.0)))
                
                # Simple scoring algorithm
                score = 50.0  # Base score
                
                # Adjust based on CPM (lower is better for cost efficiency)
                if cpm > 0:
                    if cpm < 5.0:
                        score += 20
                    elif cpm < 10.0:
                        score += 10
                    elif cpm > 20.0:
                        score -= 10
                
                # Adjust based on CTR (higher is better)
                if ctr > 0:
                    if ctr > 2.0:
                        score += 20
                    elif ctr > 1.0:
                        score += 10
                    elif ctr < 0.5:
                        score -= 10
                
                # Adjust based on conversion rate (higher is better)
                if conversion_rate > 0:
                    if conversion_rate > 5.0:
                        score += 20
                    elif conversion_rate > 2.0:
                        score += 10
                    elif conversion_rate < 1.0:
                        score -= 10
                
                # Clamp score to 0-100 range
                score = max(0, min(100, score))
                
                # Determine status
                if score >= 80:
                    status = 'Good'
                elif score >= 60:
                    status = 'Moderate'
                else:
                    status = 'Poor'
                
                # Create result
                result = {
                    'Domain': domain,
                    'Publisher': publisher,
                    'CPM': cpm,
                    'CTR': ctr,
                    'Conv Rate': conversion_rate,
                    'Score': score,
                    'Status': status
                }
                results.append(result)
            
            logger.info(f"✅ Synchronous fallback scoring generated {len(results)} results")
            
            return {
                'results': {
                    'standard_scoring_results': results,
                    'metadata': {
                        'source': 'Fallback',
                        'channel': campaign_config.get('channel', 'Unknown'),
                        'method': 'Basic scoring (enhanced engine failed)'
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Synchronous fallback scoring also failed: {e}")
            # Return minimal results to prevent complete failure
            return {
                'results': {
                    'standard_scoring_results': [],
                    'metadata': {
                        'source': 'Error',
                        'channel': 'Unknown',
                        'method': 'Scoring failed completely',
                        'error': str(e)
                    }
                }
            }
    
    async def _batch_create_score_data(
        self, 
        standard_results: List[Dict], 
        report_id: str, 
        enhanced_results: Dict
    ) -> List[Dict]:
        """Create score data dictionaries (not database objects) for better performance"""
        
        score_data = []
        
        for result in standard_results:
            # Convert Enhanced Scoring Engine format to data format
            score_data_item = await self._create_score_data_from_enhanced_result(
                result, report_id, enhanced_results
            )
            score_data.append(score_data_item)
            
        logger.info(f"📦 Processed {len(score_data)} score data items")
        
        return score_data
    
    async def _create_score_data_from_enhanced_result(
        self, 
        enhanced_result: Dict, 
        report_id: str, 
        full_results: Dict
    ) -> Dict:
        """Convert Enhanced Scoring Engine result to data dictionary (not database object)"""
        
        # Map Enhanced Scoring Engine format to data format
        domain = enhanced_result.get('Domain', 'Unknown')
        publisher = enhanced_result.get('Publisher', 'Unknown')
        cpm = float(enhanced_result.get('CPM', 0.0))
        ctr = float(enhanced_result.get('CTR', 0.0))  # Already in percentage
        conversion_rate = float(enhanced_result.get('Conv Rate', 0.0))  # Already in percentage
        score = float(enhanced_result.get('Score', 0.0))
        
        # Determine status based on score
        if score >= 80:
            status = 'Good'
        elif score >= 60:
            status = 'Moderate'
        else:
            status = 'Poor'
        
        # Get metadata from full results
        metadata = full_results.get('results', {}).get('metadata', {})
        source = metadata.get('source', 'Unknown')
        channel = metadata.get('channel', 'Unknown')
        
        # Create explanation using Enhanced Scoring Engine insights
        explanation = f"Enhanced Score {score:.1f} - {source} {channel} analysis with advanced weighting"
        
        # Create data dictionary (not database object)
        score_data = {
            'report_id': report_id,
            'domain': domain,
            'publisher': publisher,
            'cpm': cpm,
            'ctr': ctr,
            'conversion_rate': conversion_rate,
            'score': score,
            'status': status,
            'explanation': explanation
        }
        
        return score_data
    
    async def _convert_cached_to_data_format(
        self, 
        cached_results: Dict, 
        report_id: str, 
        campaign_config: Dict
    ) -> List[Dict]:
        """Convert cached results to data format (not database format)"""
        standard_results = cached_results.get('results', {}).get('standard_scoring_results', [])
        
        if not standard_results:
            return []
        
        # Convert to data format
        score_data = []
        for result in standard_results:
            score_data_item = await self._create_score_data_from_enhanced_result(
                result, report_id, cached_results
            )
            score_data.append(score_data_item)
        
        return score_data
    
    async def _generate_cache_key(self, file_content: bytes, campaign_config: Dict) -> str:
        """Generate cache key based on file content and campaign config"""
        import hashlib
        
        # Create hash of file content + campaign config
        content_hash = hashlib.md5(file_content).hexdigest()
        config_str = f"{campaign_config.get('goal')}_{campaign_config.get('channel')}_{campaign_config.get('ctr_sensitive')}"
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        return f"scoring_cache:{content_hash}:{config_hash}"
    
    async def _get_cached_results(self, cache_key: str) -> Optional[Dict]:
        """Get cached scoring results"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                import json
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    async def _cache_results(self, cache_key: str, results: Dict):
        """Cache scoring results for future use"""
        if not self.redis_client:
            return
        
        try:
            import json
            # Cache for 1 hour (3600 seconds)
            await self.redis_client.setex(
                cache_key, 
                3600, 
                json.dumps(results, default=str)
            )
            logger.info(f"💾 Results cached with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

class AsyncScoringQueue:
    """
    Async scoring queue for background processing
    """
    
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.results_cache = {}
        self.is_running = False
    
    async def start_worker(self):
        """Start background scoring worker"""
        self.is_running = True
        logger.info("🚀 Starting background scoring worker...")
        
        while self.is_running:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                if task is None:
                    continue
                
                # Process task
                await self._process_scoring_task(task)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in scoring worker: {e}")
    
    async def _process_scoring_task(self, task: Dict):
        """Process a scoring task"""
        try:
            report_id = task['report_id']
            file_content = task['file_content']
            filename = task['filename']
            campaign_config = task['campaign_config']
            
            # Process with optimization
            processor = OptimizedScoringProcessor()
            await processor.initialize_redis()
            
            results = await processor.process_file_optimized(
                file_content, filename, report_id, campaign_config
            )
            
            # Store results
            self.results_cache[report_id] = results
            
            logger.info(f"✅ Background scoring completed for report {report_id}")
            
        except Exception as e:
            logger.error(f"Error processing scoring task: {e}")
            # Store error in results
            self.results_cache[task['report_id']] = {'error': str(e)}
    
    async def add_task(self, task: Dict):
        """Add scoring task to queue"""
        await self.processing_queue.put(task)
    
    def get_results(self, report_id: str) -> Optional[Dict]:
        """Get results for a report"""
        return self.results_cache.get(report_id)
    
    async def stop_worker(self):
        """Stop background scoring worker"""
        self.is_running = False
        await self.processing_queue.put(None)
