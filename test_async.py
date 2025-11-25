#!/usr/bin/env python3
"""
Test script to verify async server handles requests correctly.
Tests fragmented requests, pipelined requests, and keep-alive.
"""

import asyncio
import time

async def test_basic_request():
    """Test basic HTTP request"""
    print("Testing basic HTTP request...")
    
    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)
    
    # Send request
    request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    writer.write(request)
    await writer.drain()
    
    # Read response
    response = await asyncio.wait_for(reader.read(4096), timeout=5.0)
    
    writer.close()
    await writer.wait_closed()
    
    response_str = response.decode('utf-8', errors='ignore')
    
    if "HTTP/1.1" in response_str and "200 OK" in response_str:
        print("  ✅ PASS: Basic request works\n")
        return True
    else:
        print(f"  ❌ FAIL: Invalid response\n")
        return False

async def test_fragmented_request():
    """Test fragmented HTTP request"""
    print("Testing fragmented request...")
    
    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)
    
    # Send request in fragments
    fragments = [
        b"GET /",
        b" HTTP/",
        b"1.1\r\n",
        b"Host: localhost",
        b"\r\n\r\n"
    ]
    
    for i, fragment in enumerate(fragments):
        print(f"  Sending fragment {i+1}/{len(fragments)}")
        writer.write(fragment)
        await writer.drain()
        await asyncio.sleep(0.05)
    
    # Read response
    response = await asyncio.wait_for(reader.read(4096), timeout=5.0)
    
    writer.close()
    await writer.wait_closed()
    
    response_str = response.decode('utf-8', errors='ignore')
    
    if "HTTP/1.1" in response_str:
        print("  ✅ PASS: Fragmented request handled correctly\n")
        return True
    else:
        print("  ❌ FAIL: Fragmented request failed\n")
        return False

async def test_pipelined_requests():
    """Test pipelined HTTP requests"""
    print("Testing pipelined requests...")
    
    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)
    
    # Send two requests at once
    pipelined = (
        b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )
    
    writer.write(pipelined)
    await writer.drain()
    
    # Read responses
    response = await asyncio.wait_for(reader.read(8192), timeout=5.0)
    
    writer.close()
    await writer.wait_closed()
    
    response_str = response.decode('utf-8', errors='ignore')
    response_count = response_str.count("HTTP/1.1")
    
    print(f"  Found {response_count} HTTP responses")
    
    if response_count >= 2:
        print("  ✅ PASS: Pipelined requests handled correctly\n")
        return True
    else:
        print(f"  ❌ FAIL: Expected 2 responses, got {response_count}\n")
        return False

async def test_keep_alive():
    """Test keep-alive with sequential requests"""
    print("Testing keep-alive...")
    
    reader, writer = await asyncio.open_connection('127.0.0.1', 8080)
    
    success_count = 0
    
    for i in range(5):
        print(f"  Sending request {i+1}/5")
        
        request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        writer.write(request)
        await writer.drain()
        
        # Read response
        response = b""
        while True:
            chunk = await asyncio.wait_for(reader.read(1024), timeout=2.0)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
        
        if b"HTTP/1.1" in response:
            success_count += 1
        
        await asyncio.sleep(0.1)
    
    writer.close()
    await writer.wait_closed()
    
    print(f"  Successfully received {success_count}/5 responses")
    
    if success_count >= 4:
        print("  ✅ PASS: Keep-alive working correctly\n")
        return True
    else:
        print(f"  ❌ FAIL: Only {success_count}/5 requests succeeded\n")
        return False

async def test_concurrent_connections():
    """Test multiple concurrent connections"""
    print("Testing 100 concurrent connections...")
    
    async def make_request(client_id):
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', 8080)
            
            request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
            writer.write(request)
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            
            writer.close()
            await writer.wait_closed()
            
            if b"HTTP/1.1" in response:
                return True
            return False
        except Exception as e:
            print(f"  Client {client_id} error: {e}")
            return False
    
    start_time = time.time()
    tasks = [make_request(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time
    
    success_count = sum(results)
    
    print(f"  Completed in {elapsed:.2f}s")
    print(f"  Successful: {success_count}/100")
    
    if success_count >= 95:
        print("  ✅ PASS: Concurrent connections handled correctly\n")
        return True
    else:
        print(f"  ❌ FAIL: Only {success_count}/100 succeeded\n")
        return False

async def main():
    print("="*60)
    print("Async HTTP Server Test Suite")
    print("="*60)
    print()
    
    try:
        # Test connection
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', 8080),
            timeout=2.0
        )
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to server at 127.0.0.1:8080")
        print(f"Error: {e}")
        print("\nMake sure the server is running with: cargo run")
        return
    
    results = []
    
    results.append(("Basic Request", await test_basic_request()))
    results.append(("Fragmented Request", await test_fragmented_request()))
    results.append(("Pipelined Requests", await test_pipelined_requests()))
    results.append(("Keep-Alive", await test_keep_alive()))
    results.append(("Concurrent Connections", await test_concurrent_connections()))
    
    # Summary
    print("="*60)
    print("Test Summary")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())
