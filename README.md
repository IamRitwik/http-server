# Rust HTTP/1.1 Web Server

A lightweight, multithreaded HTTP/1.1 web server implementation written in pure Rust with no external dependencies. This server demonstrates core concepts of network programming, concurrent request handling, and HTTP protocol implementation.

## Features

- **HTTP/1.1 Protocol Support**: Implements the HTTP/1.1 protocol with proper request parsing and response formatting
- **Multithreaded Architecture**: Uses a custom thread pool to handle multiple concurrent connections efficiently
- **Static File Serving**: Serves HTML, CSS, and JavaScript files from a configurable public directory
- **Security**: Built-in protection against directory traversal attacks
- **Content Type Detection**: Automatically sets appropriate Content-Type headers for different file types
- **Error Handling**: Comprehensive error handling for malformed requests and missing resources
- **HTTP Methods**: Supports GET, POST, PUT, and DELETE methods
- **Query String Parsing**: Parses and handles URL query parameters

## Architecture

The server is organized into several modular components:

- **Server**: Core TCP listener and connection handler with thread pool management
- **Thread Pool**: Custom implementation for concurrent request processing (4 worker threads by default)
- **HTTP Module**: Complete HTTP protocol implementation including:
  - Request parsing with method, path, and query string extraction
  - Response generation with status codes and headers
  - Support for multiple HTTP methods
- **Website Handler**: Static file server with content type detection and security features

## Prerequisites

- Rust 1.75 or later (uses Rust 2024 edition)
- Cargo (comes with Rust)

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone <your-repository-url>
cd http-server
```

## Building

Compile the project in release mode for optimal performance:

```bash
cargo build --release
```

Or compile in debug mode for development:

```bash
cargo build
```

## Running

### Default Configuration

Run the server with default settings (serves files from `./public` on `127.0.0.1:8080`):

```bash
cargo run --release
```

### Custom Public Directory

Set a custom directory for serving static files using the `PUBLIC_PATH` environment variable:

```bash
PUBLIC_PATH=/path/to/your/public cargo run --release
```

### Development Mode

Run in debug mode with hot-reloading support:

```bash
cargo run
```

## Usage

Once the server is running, you can access it via:

- Browser: Navigate to `http://127.0.0.1:8080`
- cURL: `curl http://127.0.0.1:8080`

The server will automatically serve `index.html` for the root path (`/`) and other files based on their requested paths.

### Example Requests

```bash
# Get the index page
curl http://127.0.0.1:8080/

# Get a specific file
curl http://127.0.0.1:8080/style.css

# Get with query parameters
curl http://127.0.0.1:8080/search?q=rust&category=web
```

## Project Structure

```
http-server/
├── src/
│   ├── main.rs              # Entry point and configuration
│   ├── server.rs            # TCP server and Handler trait
│   ├── thread_pool.rs       # Custom thread pool implementation
│   ├── website_handler.rs   # Static file serving logic
│   └── http/
│       ├── mod.rs           # HTTP module exports
│       ├── method.rs        # HTTP method enum (GET, POST, etc.)
│       ├── request.rs       # Request parsing logic
│       ├── response.rs      # Response generation
│       ├── status_code.rs   # HTTP status codes
│       └── query_string.rs  # Query parameter parsing
├── public/                  # Static files directory
│   ├── index.html
│   └── style.css
├── Cargo.toml
└── README.md
```

## Configuration

### Server Address

To change the server address and port, modify the following line in `src/main.rs`:

```rust
let server: Server = Server::new("127.0.0.1:8080");
```

### Thread Pool Size

Adjust the number of worker threads by modifying `src/server.rs`:

```rust
pool: ThreadPool::new(4),  // Change 4 to your desired thread count
```

## Supported HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Malformed request
- `404 Not Found`: Resource not found

## Security Features

- **Directory Traversal Protection**: The server validates all file paths to prevent access to files outside the public directory
- **Path Canonicalization**: Uses Rust's `canonicalize()` to resolve symbolic links and prevent escape attempts

## Development

### Running Tests

```bash
cargo test
```

### Code Formatting

```bash
cargo fmt
```

### Linting

```bash
cargo clippy
```

## How It Works

1. The server binds to a TCP socket and listens for incoming connections
2. Each connection is accepted and handed off to a worker thread from the pool
3. The worker reads the request data from the TCP stream
4. The request is parsed into method, path, and query string components
5. The website handler processes the request and generates an appropriate response
6. The response is sent back to the client with proper HTTP headers
7. The connection is kept alive for potential subsequent requests

## Limitations

- HTTP/1.1 only (no HTTP/2 or HTTP/3 support)
- No HTTPS/TLS support
- Limited to static file serving (no dynamic content generation)
- Basic content type detection (HTML, CSS, JS only)

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the server.

## License

This project is open source and available under the MIT License.

## Acknowledgments

Built as a learning project to understand low-level HTTP protocol implementation and concurrent server design in Rust.
