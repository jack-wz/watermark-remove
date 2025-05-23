// Defines the EnrichmentFunction trait for Rust plugins.
// Assumes serde_json::Value for dynamic data structures.
// The EKB platform or the SDK crate itself would need to include `serde_json` as a dependency.

// To use Value, you'd typically have:
// use serde_json::Value;

/// Trait for Enrichment Function plugins in Rust.
///
/// Enrichment Functions take a single data record (as a `serde_json::Value`)
/// and return an enriched or transformed version of it.
pub trait EnrichmentFunction {
    /// Processes a single data record and returns the modified record.
    ///
    /// # Arguments
    /// * `data`: A `serde_json::Value` representing the input data record.
    /// * `config`: A `serde_json::Value` containing configuration parameters
    ///             specific to this function's operation.
    ///
    /// # Returns
    /// A `Result<serde_json::Value, String>` containing the processed data record
    /// or an error message if processing fails.
    fn process(&self, data: serde_json::Value, config: &serde_json::Value) -> Result<serde_json::Value, String>;
}

// Example (conceptual, would be in a separate plugin crate):
// struct MyExampleRustFunction;
// impl EnrichmentFunction for MyExampleRustFunction {
//     fn process(&self, mut data: serde_json::Value, config: &serde_json::Value) -> Result<serde_json::Value, String> {
//         if let serde_json::Value::Object(mut map) = data {
//             map.insert("rust_processed".to_string(), serde_json::json!(true));
//             Ok(serde_json::Value::Object(map))
//         } else {
//             Err("Input data must be an object".to_string())
//         }
//     }
// }
