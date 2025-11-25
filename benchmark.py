#!/usr/bin/env python3
"""
Benchmark script to test HTTP server performance.
Tests requests per second with varying concurrency levels.
"""

import asyncio
import aiohttp
import time
from statistics import mean, median, stdev

async def make_request(session, url):
    """Make a single HTTP request and return latency"""
    start = time.time()
    try:
        async with session.get(url) as response:
            await response.read()
            latency = (time.time() - start) * 1000  # Convert to ms
            return latency, response.status == 200
    except Exception as e:
        return None, False

async def benchmark(url, total_requests, concurrency):
    """Run benchmark with specified concurrency"""
    print(f"\n{'='*60}")
    print(f"Benchmark: {total_requests} requests, {concurrency} concurrent")
    print(f"{'='*60}")
    
    latencies = []
    successes = 0
    failures = 0
    
    start_time = time.time()
    
    connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=concurrency)
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Create batches of concurrent requests
        for i in range(0, total_requests, concurrency):
            batch_size = min(concurrency, total_requests - i)
            tasks = [make_request(session, url) for _ in range(batch_size)]
            results = await asyncio.gather(*tasks)
            
            for latency, success in results:
                if success and latency is not None:
                    latencies.append(latency)
                    successes += 1
                else:
                    failures += 1
            
            # Progress indicator
            completed = i + batch_size
            if completed % 100 == 0 or completed == total_requests:
                print(f"  Progress: {completed}/{total_requests} requests completed")
    
    elapsed = time.time() - start_time
    
    # Calculate statistics
    if latencies:
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg_latency = mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        std_latency = stdev(latencies) if len(latencies) > 1 else 0
    else:
        p50 = p95 = p99 = avg_latency = min_latency = max_latency = std_latency = 0
    
    req_per_sec = total_requests / elapsed if elapsed > 0 else 0
    
    # Print results
    print(f"\n📊 Results:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Requests/sec: {req_per_sec:.2f}")
    print(f"  Successful: {successes}/{total_requests} ({successes/total_requests*100:.1f}%)")
    print(f"  Failed: {failures}/{total_requests}")
    
    print(f"\n⏱️  Latency (ms):")
    print(f"  Min: {min_latency:.2f}")
    print(f"  Avg: {avg_latency:.2f}")
    print(f"  p50: {p50:.2f}")
    print(f"  p95: {p95:.2f}")
    print(f"  p99: {p99:.2f}")
    print(f"  Max: {max_latency:.2f}")
    print(f"  StdDev: {std_latency:.2f}")
    
    return {
        'req_per_sec': req_per_sec,
        'elapsed': elapsed,
        'successes': successes,
        'failures': failures,
        'latencies': {
            'min': min_latency,
            'avg': avg_latency,
            'p50': p50,
            'p95': p95,
            'p99': p99,
            'max': max_latency,
            'stddev': std_latency
        }
    }

async def main():
    url = "http://127.0.0.1:8080/"
    
    print("="*60)
    print("HTTP Server Performance Benchmark")
    print("="*60)
    print(f"Target URL: {url}")
    
    # Test connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"⚠️  Warning: Server returned status {response.status}")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to server at {url}")
        print(f"Error: {e}")
        print("\nMake sure the server is running with: cargo run")
        return
    
    results = []
    
    # Benchmark 1: Warm-up
    print("\n🔥 Warm-up run...")
    await benchmark(url, 100, 10)
    
    # Benchmark 2: Low concurrency
    result = await benchmark(url, 1000, 10)
    results.append(("1000 requests, 10 concurrent", result))
    
    # Benchmark 3: Medium concurrency
    result = await benchmark(url, 1000, 100)
    results.append(("1000 requests, 100 concurrent", result))
    
    # Benchmark 4: High concurrency
    result = await benchmark(url, 1000, 500)
    results.append(("1000 requests, 500 concurrent", result))
    
    # Benchmark 5: Very high concurrency (stress test)
    result = await benchmark(url, 10000, 1000)
    results.append(("10000 requests, 1000 concurrent", result))
    
    # Summary
    print(f"\n\n{'='*60}")
    print("📈 BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"{'Test':<35} {'Req/s':<12} {'p50 (ms)':<12} {'p99 (ms)':<12}")
    print(f"{'-'*60}")
    
    for name, result in results:
        print(f"{name:<35} {result['req_per_sec']:<12.2f} {result['latencies']['p50']:<12.2f} {result['latencies']['p99']:<12.2f}")
    
    # Check if we hit 10k req/s target
    max_rps = max(r[1]['req_per_sec'] for r in results)
    print(f"\n{'='*60}")
    if max_rps >= 10000:
        print(f"✅ SUCCESS: Peak performance {max_rps:.2f} req/s (target: 10,000 req/s)")
    else:
        print(f"⚠️  Peak performance {max_rps:.2f} req/s (target: 10,000 req/s)")
        print(f"   Achieved {max_rps/10000*100:.1f}% of target")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
