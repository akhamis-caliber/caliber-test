#!/usr/bin/env python3
"""
Cache monitoring script for Caliber application
Helps debug Redis cache performance and usage
"""

import redis
import json
import time
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.settings import settings

def monitor_cache():
    """Monitor Redis cache performance and usage"""
    try:
        # Connect to Redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("✅ Redis connection successful")
        
        # Get basic info
        info = r.info()
        print(f"\n📊 Redis Server Info:")
        print(f"  Version: {info.get('redis_version', 'unknown')}")
        print(f"  Uptime: {info.get('uptime_in_seconds', 0)} seconds")
        print(f"  Connected clients: {info.get('connected_clients', 0)}")
        
        # Memory usage
        memory = r.info('memory')
        print(f"\n💾 Memory Usage:")
        print(f"  Used memory: {memory.get('used_memory_human', 'unknown')}")
        print(f"  Peak memory: {memory.get('used_memory_peak_human', 'unknown')}")
        print(f"  Memory fragmentation: {memory.get('mem_fragmentation_ratio', 'unknown')}")
        
        # Database stats
        db_size = r.dbsize()
        print(f"\n🗄️  Database Stats:")
        print(f"  Total keys: {db_size}")
        
        # Get Caliber-specific keys
        caliber_keys = r.keys("caliber:*")
        print(f"  Caliber cache keys: {len(caliber_keys)}")
        
        if caliber_keys:
            print(f"\n🔑 Caliber Cache Keys:")
            for key in sorted(caliber_keys[:10]):  # Show first 10
                key_str = key.decode('utf-8')
                ttl = r.ttl(key)
                size = r.memory_usage(key) or 0
                print(f"  {key_str}")
                print(f"    TTL: {ttl}s, Size: {size} bytes")
            
            if len(caliber_keys) > 10:
                print(f"  ... and {len(caliber_keys) - 10} more keys")
        
        # Performance test
        print(f"\n⚡ Performance Test:")
        test_key = "caliber:test_performance"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        # Test write performance
        start_time = time.time()
        r.setex(test_key, 60, json.dumps(test_data))
        write_time = (time.time() - start_time) * 1000
        print(f"  Write time: {write_time:.2f}ms")
        
        # Test read performance
        start_time = time.time()
        result = r.get(test_key)
        read_time = (time.time() - start_time) * 1000
        print(f"  Read time: {read_time:.2f}ms")
        
        # Clean up test key
        r.delete(test_key)
        
        # Cache hit rate simulation
        print(f"\n🎯 Cache Hit Rate Simulation:")
        cache_hits = 0
        cache_misses = 0
        
        for i in range(5):
            key = f"caliber:test_hit_rate_{i}"
            if r.exists(key):
                cache_hits += 1
                r.get(key)
            else:
                cache_misses += 1
                r.setex(key, 10, f"value_{i}")
        
        total_requests = cache_hits + cache_misses
        hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0
        print(f"  Cache hits: {cache_hits}/{total_requests} ({hit_rate:.1f}%)")
        
        # Clean up test keys
        for i in range(5):
            r.delete(f"caliber:test_hit_rate_{i}")
        
        print(f"\n✅ Cache monitoring completed successfully")
        
    except redis.ConnectionError:
        print("❌ Failed to connect to Redis")
        print("Make sure Redis is running and accessible")
    except Exception as e:
        print(f"❌ Error monitoring cache: {e}")

if __name__ == "__main__":
    monitor_cache()

