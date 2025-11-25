use crate::http::ParseError;
use std::str::FromStr;

#[derive(Debug)]
pub enum Method {
    GET,
    DELETE,
    POST,
    PUT,
}

impl FromStr for Method {
    type Err = ParseError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "GET" => Ok(Method::GET),
            "DELETE" => Ok(Method::DELETE),
            "POST" => Ok(Method::POST),
            "PUT" => Ok(Method::PUT),
            _ => Err(ParseError::InvalidMethod),
        }
    }
}

impl std::fmt::Display for Method {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Method::GET => write!(f, "GET"),
            Method::DELETE => write!(f, "DELETE"),
            Method::POST => write!(f, "POST"),
            Method::PUT => write!(f, "PUT"),
        }
    }
}
