use crate::http::{ParseError, Request, Response, StatusCode};
use std::sync::Arc;
use tokio::io::AsyncReadExt;
use tokio::net::TcpListener;

pub trait Handler: Send + Sync {
    fn handle_request(&self, request: &Request) -> Response;

    fn handle_bad_request(&self, e: &ParseError) -> Response {
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
}

impl Server {
    pub fn new(addr: &str) -> Self {
        Self {
            addr: addr.to_string(),
        }
    }

    pub fn addr(&self) -> &str {
        &self.addr
    }

    pub async fn run(self, handler: impl Handler + 'static) {
        println!("Server running on {}", self.addr);
        let listener = TcpListener::bind(&self.addr).await.unwrap();
        let handler = Arc::new(handler);

        loop {
            match listener.accept().await {
                Ok((mut stream, addr)) => {
                    println!("Incoming connection from => {}", addr);
                    let handler = Arc::clone(&handler);

                    tokio::spawn(async move {
                        // Set read timeout to prevent indefinite blocking
                        // Note: Tokio doesn't use set_read_timeout, we'll use tokio::time::timeout instead

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

                            // Read more data from the socket with timeout
                            let read_result = tokio::time::timeout(
                                tokio::time::Duration::from_secs(30),
                                stream.read(&mut read_buffer),
                            )
                            .await;

                            match read_result {
                                Ok(Ok(0)) => {
                                    println!("Connection closed by client: {}", addr);
                                    break;
                                }
                                Ok(Ok(bytes_read)) => {
                                    println!("Received {} bytes from {}", bytes_read, addr);

                                    // Append new data to the request buffer
                                    request_buffer.extend_from_slice(&read_buffer[..bytes_read]);

                                    // Check for buffer overflow
                                    if request_buffer.len() > MAX_REQUEST_SIZE {
                                        println!(
                                            "Request too large from {}, closing connection",
                                            addr
                                        );
                                        let response = Response::new(
                                            StatusCode::BadRequest,
                                            Some("<h4>Request Too Large</h4>".to_string()),
                                            None,
                                        );
                                        let _ = response.send(&mut stream).await;
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
                                                let response =
                                                    match Request::try_from(request_bytes) {
                                                        Ok(request) => {
                                                            println!(
                                                                "Parsed request: {} {}",
                                                                request.method(),
                                                                request.path()
                                                            );
                                                            handler.handle_request(&request)
                                                        }
                                                        Err(e) => {
                                                            println!(
                                                                "Failed to parse request: {}",
                                                                e
                                                            );
                                                            handler.handle_bad_request(&e)
                                                        }
                                                    };

                                                // Send the response
                                                if let Err(e) = response.send(&mut stream).await {
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
                                Ok(Err(e)) => {
                                    println!("Failed to read from connection {}: {}", addr, e);
                                    break;
                                }
                                Err(_) => {
                                    // Timeout occurred
                                    println!("Read timeout on connection from {}, closing", addr);
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
