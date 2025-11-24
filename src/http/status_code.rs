use std::fmt::{Debug, Display, Formatter, Result as FmtResult};

#[derive(Copy, Clone)]
pub enum StatusCode {
    Ok = 200,
    NotFound = 404,
    BadRequest = 400,
}

impl StatusCode {
    pub fn reason_phrase(&self) -> &str {
        match self {
            Self::Ok => "OK",
            Self::NotFound => "Not Found",
            Self::BadRequest => "Bad Request",
        }
    }
}

impl Display for StatusCode {
    fn fmt(&self, f: &mut Formatter) -> FmtResult {
        write!(f, "{}", *self as u16)
    }
}

impl Debug for StatusCode {
    fn fmt(&self, f: &mut Formatter) -> FmtResult {
        write!(f, "{}", *self as u16)
    }
}
