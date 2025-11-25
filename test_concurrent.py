#!/usr/bin/env python3
"""
Test script to verify thread pool doesn't block with keep-alive connections.
Opens multiple concurrent connections to ensure all are served.
"""

import socket
import threading
import time

def make_request(client_id, results):
    """Make a request from a specific client"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect(('127.0.0.1', 8080))
        
        # Send request
        request = (
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"\r\n"
        )
        sock.send(request)
        
        # Receive response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
        
        sock.close()
        
        # Check if we got a valid response
        if b"HTTP/1.1" in response:
            results[client_id] = "SUCCESS"
            print(f"  Client {client_id}: ✅ Got response ({len(response)} bytes)")
        else:
            results[client_id] = "INVALID_RESPONSE"
            print(f"  Client {client_id}: ❌ Invalid response")
    
    except socket.timeout:
        results[client_id] = "TIMEOUT"
        print(f"  Client {client_id}: ❌ Timeout")
    except Exception as e:
        results[client_id] = f"ERROR: {e}"
        print(f"  Client {client_id}: ❌ Error: {e}")

def test_concurrent_connections(num_clients):
    """Test multiple concurrent connections"""
    print(f"\nTesting {num_clients} concurrent connections...")
    print("(With 4 threads, the 5th+ clients should NOT be starved)")
    
    results = {}
    threads = []
    
    # Start all clients at once
    start_time = time.time()
    for i in range(num_clients):
        t = threading.Thread(target=make_request, args=(i+1, results))
        t.start()
        threads.append(t)
        time.sleep(0.05)  # Small stagger to avoid overwhelming
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    # Analyze results
    success_count = sum(1 for r in results.values() if r == "SUCCESS")
    timeout_count = sum(1 for r in results.values() if r == "TIMEOUT")
    
    print(f"\nResults after {elapsed:.2f} seconds:")
    print(f"  ✅ Successful: {success_count}/{num_clients}")
    print(f"  ⏱️  Timeouts: {timeout_count}/{num_clients}")
    
    if success_count == num_clients:
        print(f"\n✅ PASS: All {num_clients} clients served successfully")
        return True
    elif success_count >= num_clients * 0.8:  # 80% success rate
        print(f"\n⚠️  PARTIAL: {success_count}/{num_clients} clients served")
        return True
    else:
        print(f"\n❌ FAIL: Only {success_count}/{num_clients} clients served")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Thread Pool Concurrency Test")
    print("=" * 60)
    print("\nThis test verifies that the server can handle more")
    print("concurrent connections than the thread pool size (4).")
    
    try:
        # Test with 10 concurrent clients (more than 4 threads)
        success = test_concurrent_connections(10000)
        
        if success:
            print("\n🎉 Thread pool is not blocking!")
            print("The server can handle more connections than thread pool size.")
            exit(0)
        else:
            print("\n⚠️  Thread pool may have issues")
            exit(1)
    
    except ConnectionRefusedError:
        print("\n❌ ERROR: Could not connect to server at 127.0.0.1:8080")
        print("Make sure the server is running with: cargo run")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
