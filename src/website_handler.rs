use std::fs;

use crate::{
    http::{Method, Request, Response, StatusCode},
    server::Handler,
};

pub struct WebsiteHandler {
    public_path: String,
}

impl WebsiteHandler {
    pub fn new(public_path: String) -> Self {
        Self { public_path }
    }

    fn read_file(&self, file_path: &str) -> Option<String> {
        let full_path = format!("{}{}", self.public_path, file_path);
        match fs::canonicalize(full_path) {
            Ok(path) => {
                if path.starts_with(&self.public_path) {
                    fs::read_to_string(path).ok()
                } else {
                    println!("Directory traversal attack detected {}", path.display());
                    None
                }
            }
            Err(_) => None,
        }
    }
}

impl Handler for WebsiteHandler {
    fn handle_request(&self, request: &Request) -> Response {
        match (request.method(), request.path()) {
            (Method::GET, "/") => Response::new(
                StatusCode::Ok,
                self.read_file("/index.html"),
                Some("text/html".to_string()),
            ),
            (Method::GET, path) => match self.read_file(path) {
                Some(contents) => {
                    let content_type = if path.ends_with(".css") {
                        "text/css"
                    } else if path.ends_with(".js") {
                        "text/javascript"
                    } else {
                        "text/html"
                    };
                    Response::new(
                        StatusCode::Ok,
                        Some(contents),
                        Some(content_type.to_string()),
                    )
                }
                None => Response::new(
                    StatusCode::NotFound,
                    Some("<h3> Not Found</h3>".to_string()),
                    None,
                ),
            },
            _ => Response::new(
                StatusCode::NotFound,
                Some("<h3> Not Found</h3>".to_string()),
                None,
            ),
        }
    }
}
