#![allow(dead_code)]
use std::env;

use server::Server;

use crate::website_handler::WebsiteHandler;

mod http;
mod server;
mod thread_pool;
mod website_handler;

fn main() {
    let default_path = format!("{}/public", env!("CARGO_MANIFEST_DIR"));
    let public_path = env::var("PUBLIC_PATH").unwrap_or(default_path);
    println!("Public path: {}", public_path);
    // server here is struct
    let server: Server = Server::new("127.0.0.1:8080");
    let port: &str = &server.addr()[10..];
    let ip: &str = &server.addr()[..9];
    println!("IP address: {} and Port: {}", ip, port);
    server.run(WebsiteHandler::new(public_path));
}
