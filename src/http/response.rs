use crate::http::StatusCode;
use std::{
    io::{Result as IoResult, Write},
    net::TcpStream,
};

pub struct Response {
    status_code: StatusCode,
    body: Option<String>,
    content_type: Option<String>,
}

impl Response {
    pub fn new(
        status_code: StatusCode,
        body: Option<String>,
        content_type: Option<String>,
    ) -> Self {
        Self {
            status_code,
            body,
            content_type,
        }
    }

    pub fn send(&self, stream: &mut TcpStream) -> IoResult<()> {
        let body = match &self.body {
            Some(body) => body,
            None => "",
        };
        let content_type = match &self.content_type {
            Some(ct) => ct,
            None => "text/html",
        };
        write!(
            stream,
            "HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n\r\n{}",
            self.status_code,
            self.status_code.reason_phrase(),
            content_type,
            body.len(),
            body
        )
    }
}
