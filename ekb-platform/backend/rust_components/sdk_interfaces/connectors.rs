// Defines the SourceConnector trait for Rust plugins.
// Assumes serde_json::Value for dynamic data structures.
// The EKB platform or the SDK crate itself would need to include `serde_json` as a dependency.

// To use Value, you'd typically have:
// use serde_json::Value;
// For this placeholder, we'll write it as if `serde_json::Value` is available
// under that path or as just `Value` if `use serde_json::Value;` is present.

/// Trait for Source Connector plugins in Rust.
///
/// Source Connectors are responsible for fetching data from various external
/// or internal systems.
pub trait SourceConnector {
    /// Initializes the connector and establishes any necessary connections
    /// to the data source using the provided configuration.
    ///
    /// This method is called once when the plugin is loaded or a flow
    /// utilizing this connector starts.
    ///
    /// # Arguments
    /// * `config`: A `serde_json::Value` containing configuration parameters
    ///             specific to this connector instance.
    ///
    /// # Errors
    /// Returns an `Err(String)` if initialization or connection fails.
    fn connect(&mut self, config: &serde_json::Value) -> Result<(), String>;

    /// Reads data from the source and returns an iterator of records.
    ///
    /// Each record is itself a `Result<serde_json::Value, String>` to allow for
    /// per-record error handling during data retrieval. The iterator allows for
    /// streaming data.
    ///
    /// # Returns
    /// A `Box<dyn Iterator<Item = Result<serde_json::Value, String>>>` which
    /// yields data records.
    fn read_data(&mut self) -> Box<dyn Iterator<Item = Result<serde_json::Value, String>>>;

    /// Returns a `serde_json::Value` representing the schema of the data records
    /// produced by this connector. This could be a JSON Schema or a custom
    /// schema structure.
    ///
    /// # Errors
    /// Returns an `Err(String)` if the schema cannot be determined or generated.
    fn schema(&self) -> Result<serde_json::Value, String>;

    /// Closes any open connections and performs necessary cleanup operations.
    ///
    /// This method is called when the plugin is unloaded or a flow utilizing
    /// this connector finishes its execution.
    ///
    /// # Errors
    /// Returns an `Err(String)` if closing or cleanup fails.
    fn close(&mut self) -> Result<(), String>;
}

// Example (conceptual, would be in a separate plugin crate):
// struct MyExampleRustConnector { client: Option<String> }
// impl SourceConnector for MyExampleRustConnector {
//     fn connect(&mut self, config: &serde_json::Value) -> Result<(), String> { Ok(()) }
//     fn read_data(&mut self) -> Box<dyn Iterator<Item = Result<serde_json::Value, String>>> {
//         let data: Vec<Result<serde_json::Value, String>> = vec![Ok(serde_json::json!({"id": 1}))];
//         Box::new(data.into_iter())
//     }
//     fn schema(&self) -> Result<serde_json::Value, String> { Ok(serde_json::json!({"type": "object"})) }
//     fn close(&mut self) -> Result<(), String> { Ok(()) }
// }
