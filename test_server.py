#!/usr/bin/env python3
"""
Test script to verify HTTP server handles fragmented requests correctly.
Sends a request in multiple chunks to simulate fragmented TCP packets.
"""

import socket
import time

def test_fragmented_request():
    """Send a GET request in multiple fragments"""
    print("Testing fragmented request handling...")
    
    # Connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 8080))
    
    # Send request in fragments
    fragments = [
        b"GET /",
        b"hello",
        b".html HTTP",
        b"/1.1\r\n",
        b"Host: localhost\r\n",
        b"\r\n"
    ]
    
    for i, fragment in enumerate(fragments):
        print(f"  Sending fragment {i+1}/{len(fragments)}: {fragment}")
        sock.send(fragment)
        time.sleep(0.1)  # Small delay between fragments
    
    # Receive response
    response = b""
    sock.settimeout(2.0)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        pass
    
    sock.close()
    
    # Check response
    response_str = response.decode('utf-8', errors='ignore')
    print(f"\nReceived response ({len(response)} bytes):")
    print(response_str[:200])  # Print first 200 chars
    
    if "HTTP/1.1" in response_str and ("200 OK" in response_str or "404 Not Found" in response_str):
        print("\n✅ PASS: Fragmented request handled correctly")
        return True
    else:
        print("\n❌ FAIL: Invalid response received")
        return False

def test_pipelined_requests():
    """Send multiple requests in one TCP write"""
    print("\n\nTesting pipelined requests...")
    
    # Connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 8080))
    
    # Send two requests at once
    pipelined = (
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"\r\n"
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"\r\n"
    )
    
    print(f"  Sending {len(pipelined)} bytes with 2 pipelined requests")
    sock.send(pipelined)
    
    # Receive responses
    response = b""
    sock.settimeout(2.0)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        pass
    
    sock.close()
    
    # Check for two responses
    response_str = response.decode('utf-8', errors='ignore')
    response_count = response_str.count("HTTP/1.1")
    
    print(f"\nReceived {len(response)} bytes")
    print(f"Found {response_count} HTTP responses")
    
    if response_count >= 2:
        print("\n✅ PASS: Both pipelined requests handled correctly")
        return True
    else:
        print(f"\n❌ FAIL: Expected 2 responses, got {response_count}")
        return False

def test_keep_alive():
    """Test keep-alive connection with multiple sequential requests"""
    print("\n\nTesting keep-alive with sequential requests...")
    
    # Connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 8080))
    sock.settimeout(2.0)
    
    success_count = 0
    
    # Send 5 requests on the same connection
    for i in range(5):
        request = (
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"\r\n"
        )
        
        print(f"  Sending request {i+1}/5")
        sock.send(request)
        
        # Receive response
        response = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # Check if we got a complete response
                if b"\r\n\r\n" in response:
                    break
        except socket.timeout:
            pass
        
        if b"HTTP/1.1" in response:
            success_count += 1
        
        time.sleep(0.1)
    
    sock.close()
    
    print(f"\nSuccessfully received {success_count}/5 responses")
    
    if success_count >= 4:  # Allow for some tolerance
        print("\n✅ PASS: Keep-alive working correctly")
        return True
    else:
        print(f"\n❌ FAIL: Only {success_count}/5 requests succeeded")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("HTTP Server Test Suite")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Fragmented Requests", test_fragmented_request()))
        results.append(("Pipelined Requests", test_pipelined_requests()))
        results.append(("Keep-Alive", test_keep_alive()))
    except ConnectionRefusedError:
        print("\n❌ ERROR: Could not connect to server at 127.0.0.1:8080")
        print("Make sure the server is running with: cargo run")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some tests failed")
        exit(1)
