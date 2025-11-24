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
                        let mut buffer = [0; 1024];
                        loop {
                            match stream.read(&mut buffer) {
                                Ok(0) => {
                                    println!("Connection closed by client!!");
                                    break;
                                }
                                Ok(bytes_read) => {
                                    println!("Received {} bytes from client", bytes_read);
                                    let response = match Request::try_from(&buffer[..bytes_read]) {
                                        Ok(request) => {
                                            // println!("Request: {:?}", request);
                                            handler.lock().unwrap().handle_request(&request)
                                        }
                                        Err(e) => {
                                            println!("Failed to parse request: {}", e);
                                            handler.lock().unwrap().handle_bad_request(&e)
                                        }
                                    };
                                    if let Err(e) = response.send(&mut stream) {
                                        println!("Failed to send response: {}", e);
                                        break;
                                    }
                                }
                                Err(e) => {
                                    println!("Failed to read from connection: {}", e);
                                    break;
                                }
                            }
                        }
                    });
                }
                Err(e) => {
                    println!("Failed to accept connection: {}", e);
                }
            }
        }
    }
}
