#![allow(dead_code)]
use std::env;

use server::Server;

use crate::website_handler::WebsiteHandler;

mod http;
mod server;
mod website_handler;

fn get_public_path() -> String {
    let default_path = format!("{}/public", env!("CARGO_MANIFEST_DIR"));
    env::var("PUBLIC_PATH").unwrap_or(default_path)
}

#[tokio::main]
async fn main() {
    let public_path = get_public_path();
    println!("Public path: {}", public_path);
    let ip = "127.0.0.1";
    let port = "8080";
    println!("IP address: {} and Port: {}", ip, port);
    let addr = format!("{}:{}", ip, port);
    let server = Server::new(&addr);
    server.run(WebsiteHandler::new(public_path)).await;
}
