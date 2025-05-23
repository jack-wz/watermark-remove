// EKB Platform Rust SDK Interfaces
// This crate (conceptually) defines the traits that Rust plugins
// should implement to be compatible with the EKB platform.

// Declare modules for connectors and functions
pub mod connectors;
pub mod functions;

// Re-export key traits for easier access if this were a published crate.
// pub use connectors::SourceConnector;
// pub use functions::EnrichmentFunction;

// Note: To use serde_json::Value, the sdk_interfaces crate (or the EKB platform's
// core Rust components if these traits are defined there) would need to add
// `serde` and `serde_json` to its Cargo.toml dependencies.
// [dependencies]
// serde = { version = "1.0", features = ["derive"] }
// serde_json = "1.0"
