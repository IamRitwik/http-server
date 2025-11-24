import socket
import threading
import time

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8080

def test_keep_alive(thread_id):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            print(f"Thread {thread_id}: Connected")

            # Request 1
            request = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
            s.sendall(request.encode())
            response = s.recv(4096)
            print(f"Thread {thread_id}: Received response 1 ({len(response)} bytes)")
            
            if not response:
                print(f"Thread {thread_id}: Failed to get response 1")
                return

            time.sleep(0.5) # Simulate delay

            # Request 2 (Keep-Alive)
            s.sendall(request.encode())
            response = s.recv(4096)
            print(f"Thread {thread_id}: Received response 2 ({len(response)} bytes)")
            
            if not response:
                print(f"Thread {thread_id}: Failed to get response 2 (Keep-Alive failed)")
                return

            print(f"Thread {thread_id}: Keep-Alive Success")
    except Exception as e:
        print(f"Thread {thread_id}: Error: {e}")

threads = []
for i in range(5):
    t = threading.Thread(target=test_keep_alive, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Verification Complete")
