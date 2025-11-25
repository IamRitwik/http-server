use crate::http::{ParseError, Request, Response, StatusCode};
use crate::thread_pool::ThreadPool;
use std::convert::TryFrom;
use std::io::Read;
use std::net::TcpListener;
use std::sync::{Arc, Mutex};

pub trait Handler {
    fn handle_request(&mut self, request: &Request) -> Response;

    fn handle_bad_request(&mut self, e: &ParseError) -> Response {
        println!("Failed to parse request: {}", e);
        Response::new(
            StatusCode::BadRequest,
            Some("<h4> Bad Request </h4>".to_string()),
            None,
        )
    }
}

pub struct Server {
    addr: String,
    pool: ThreadPool,
}

impl Server {
    pub fn new(addr: &str) -> Self {
        Self {
            addr: addr.to_string(),
            pool: ThreadPool::new(4),
        }
    }

    pub fn addr(&self) -> &str {
        &self.addr
    }

    pub fn run(self, handler: impl Handler + Send + Sync + 'static) {
        println!("Server running on {}", self.addr);
        let listener = TcpListener::bind(&self.addr).unwrap();
        let handler = Arc::new(Mutex::new(handler));

        loop {
            match listener.accept() {
                Ok((mut stream, addr)) => {
                    println!("Incoming connection from => {}", addr);
                    let handler = Arc::clone(&handler);

                    self.pool.execute(move || {
                        // Set read timeout to prevent indefinite blocking
                        if let Err(e) =
                            stream.set_read_timeout(Some(std::time::Duration::from_secs(30)))
                        {
                            println!("Failed to set read timeout: {}", e);
                            return;
                        }

                        // Configuration constants
                        const READ_BUFFER_SIZE: usize = 4096;
                        const MAX_REQUEST_SIZE: usize = 1024 * 1024; // 1MB
                        const MAX_REQUESTS_PER_CONNECTION: usize = 100;

                        let mut request_buffer = Vec::new();
                        let mut read_buffer = [0u8; READ_BUFFER_SIZE];
                        let mut requests_handled = 0;

                        loop {
                            // Check if we've hit the max requests limit
                            if requests_handled >= MAX_REQUESTS_PER_CONNECTION {
                                println!(
                                    "Connection from {} reached max requests ({}), closing",
                                    addr, MAX_REQUESTS_PER_CONNECTION
                                );
                                break;
                            }

                            // Read more data from the socket
                            match stream.read(&mut read_buffer) {
                                Ok(0) => {
                                    println!("Connection closed by client: {}", addr);
                                    break;
                                }
                                Ok(bytes_read) => {
                                    println!("Received {} bytes from {}", bytes_read, addr);

                                    // Append new data to the request buffer
                                    request_buffer.extend_from_slice(&read_buffer[..bytes_read]);

                                    // Check for buffer overflow
                                    if request_buffer.len() > MAX_REQUEST_SIZE {
                                        println!("Request too large from {}, closing connection", addr);
                                        let response = Response::new(
                                            StatusCode::BadRequest,
                                            Some("<h4>Request Too Large</h4>".to_string()),
                                            None,
                                        );
                                        let _ = response.send(&mut stream);
                                        break;
                                    }

                                    // Process all complete requests in the buffer
                                    loop {
                                        // Find the boundary of the next complete request
                                        match crate::http::request::find_request_boundary(
                                            &request_buffer,
                                        ) {
                                            Some(boundary_idx) => {
                                                // We have a complete request
                                                let request_bytes = &request_buffer[..boundary_idx];

                                                // Parse and handle the request
                                                let response = match Request::try_from(request_bytes) {
                                                    Ok(request) => {
                                                        println!(
                                                            "Parsed request: {} {}",
                                                            request.method(),
                                                            request.path()
                                                        );
                                                        handler.lock().unwrap().handle_request(&request)
                                                    }
                                                    Err(e) => {
                                                        println!("Failed to parse request: {}", e);
                                                        handler.lock().unwrap().handle_bad_request(&e)
                                                    }
                                                };

                                                // Send the response
                                                if let Err(e) = response.send(&mut stream) {
                                                    println!("Failed to send response: {}", e);
                                                    break;
                                                }

                                                requests_handled += 1;

                                                // Remove the processed request from the buffer
                                                request_buffer.drain(..boundary_idx);

                                                // Check if we've hit the limit
                                                if requests_handled >= MAX_REQUESTS_PER_CONNECTION {
                                                    println!(
                                                        "Reached max requests ({}), closing connection",
                                                        MAX_REQUESTS_PER_CONNECTION
                                                    );
                                                    break;
                                                }
                                            }
                                            None => {
                                                // No complete request yet, need to read more data
                                                break;
                                            }
                                        }
                                    }
                                }
                                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                                    // Timeout occurred, close the connection
                                    println!("Read timeout on connection from {}, closing", addr);
                                    break;
                                }
                                Err(e) => {
                                    println!("Failed to read from connection {}: {}", addr, e);
                                    break;
                                }
                            }
                        }
                        println!("Connection handler for {} finished", addr);
                    });
                }
                Err(e) => {
                    println!("Failed to accept connection: {}", e);
                }
            }
        }
    }
}
