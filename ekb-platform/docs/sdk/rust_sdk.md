# EKB Platform - Rust Plugin SDK

This document outlines the development of backend plugins for the EKB Platform using Rust. Rust plugins are suitable for performance-critical tasks, system-level integrations, and ensuring memory safety.

## Interfaces (Traits)

Rust plugins implement predefined traits to ensure compatibility with the EKB platform. These traits would conceptually be defined in a crate like `ekb_platform_sdk` or directly within `ekb_platform::backend::rust_components::sdk_interfaces`. For simplicity, we'll refer to them as being in `sdk_interfaces`.

We'll use `serde_json::Value` for dynamic data structures (similar to Python's `Dict[str, Any]`) and `Result<T, String>` for error handling.

### 1. SourceConnector

A `SourceConnector` plugin fetches data from an external or internal source.

**Trait Definition (Conceptual - in `sdk_interfaces/connectors.rs`):**
```rust
// use serde_json::Value; // Requires serde and serde_json dependencies in the SDK crate

pub trait SourceConnector {
    /// Initializes the connector and establishes connections.
    /// Called once when the plugin is loaded or a flow starts.
    fn connect(&mut self, config: &serde_json::Value) -> Result<(), String>;

    /// Reads data from the source and returns an iterator of records.
    /// Each record is a Result<Value, String>.
    fn read_data(&mut self) -> Box<dyn Iterator<Item = Result<serde_json::Value, String>>>;

    /// Returns a JSON Schema describing the data records.
    fn schema(&self) -> Result<serde_json::Value, String>;

    /// Closes connections and performs cleanup.
    fn close(&mut self) -> Result<(), String>;
}
```

**Implementation Example:**
A developer would create a Rust struct and implement the `SourceConnector` trait for it.
```rust
// Example: my_custom_rust_connector/src/lib.rs
// use ekb_platform::backend::rust_components::sdk_interfaces::connectors::SourceConnector; // Conceptual path
// use serde_json::{json, Value};
// use std::error::Error; // For more robust error handling than just String

// pub struct MyRustSource {
//     config: Option<Value>,
//     data: Vec<Value>,
//     iterator_index: usize,
// }

// impl MyRustSource {
//     pub fn new() -> Self {
//         MyRustSource {
//             config: None,
//             data: vec![
//                 json!({"id": 1, "message": "Hello from Rust Source 1"}),
//                 json!({"id": 2, "message": "Hello from Rust Source 2"}),
//             ],
//             iterator_index: 0,
//         }
//     }
// }

// impl SourceConnector for MyRustSource {
//     fn connect(&mut self, config: &Value) -> Result<(), String> {
//         println!("Connecting Rust source with config: {:?}", config);
//         self.config = Some(config.clone());
//         // Perform actual connection logic here
//         Ok(())
//     }

//     fn read_data(&mut self) -> Box<dyn Iterator<Item = Result<Value, String>>> {
//         // For this example, we'll iterate over a fixed vector.
//         // A real implementation would fetch data from an external source.
//         // Reset index for multiple calls if needed, or make it a true one-shot iterator.
//         // This example is a bit naive as it consumes self.data on repeated calls to read_data
//         // without proper state management for the iterator.
//         // A better way would be to return a new iterator struct each time.
        
//         // Let's make a simple consuming iterator for this example.
//         // Note: This simple example is not robust for multiple calls to read_data.
//         // A real implementation would likely return a struct that itself implements Iterator.
//         let data_to_yield = self.data.clone(); // Clone for this example
//         let mut current_index = 0;
//         Box::new(std::iter::from_fn(move || {
//             if current_index < data_to_yield.len() {
//                 let item = data_to_yield[current_index].clone();
//                 current_index += 1;
//                 Some(Ok(item))
//             } else {
//                 None
//             }
//         }))
//     }

//     fn schema(&self) -> Result<Value, String> {
//         Ok(json!({
//             "type": "object",
//             "properties": {
//                 "id": {"type": "integer"},
//                 "message": {"type": "string"}
//             }
//         }))
//     }

//     fn close(&mut self) -> Result<(), String> {
//         println!("Closing Rust source connection.");
//         Ok(())
//     }
// }
```

### 2. EnrichmentFunction

An `EnrichmentFunction` plugin processes a single data record.

**Trait Definition (Conceptual - in `sdk_interfaces/functions.rs`):**
```rust
// use serde_json::Value;

pub trait EnrichmentFunction {
    /// Processes a single data record and returns the modified record.
    fn process(&self, data: serde_json::Value, config: &serde_json::Value) -> Result<serde_json::Value, String>;
}
```

**Implementation Example:**
```rust
// Example: my_rust_enrichment/src/lib.rs
// use ekb_platform::backend::rust_components::sdk_interfaces::functions::EnrichmentFunction; // Conceptual path
// use serde_json::{json, Value, Map};

// pub struct AddMetadataFunction;

// impl EnrichmentFunction for AddMetadataFunction {
//     fn process(&self, mut data: Value, config: &Value) -> Result<Value, String> {
//         if let Value::Object(mut map) = data {
//             let plugin_name = config.get("plugin_name").and_then(Value::as_str).unwrap_or("unknown_rust_plugin");
//             map.insert("processed_by_rust_plugin".to_string(), json!(plugin_name));
//             map.insert("rust_enriched_timestamp".to_string(), json!(chrono::Utc::now().to_rfc3339()));
//             data = Value::Object(map);
//         } else {
//             return Err("Data must be a JSON object".to_string());
//         }
//         Ok(data)
//     }
// }
```

## Plugin Discovery and Loading (FFI - Foreign Function Interface)

Rust plugins are typically compiled into dynamic libraries (`.so` on Linux, `.dylib` on macOS, `.dll` on Windows). The EKB platform's Rust components would use FFI to load and interact with these libraries. The `libloading` crate is commonly used for this.

### 1. Plugin Compilation
Rust plugin crates would be compiled as `cdylib`:
```toml
# In plugin's Cargo.toml
[lib]
crate-type = ["cdylib"] 
```

### 2. Exposing Plugin Interface
The plugin must expose C-compatible functions that the main application can call. This usually involves:
*   An initialization function that returns a pointer to a trait object (e.g., `Box<dyn SourceConnector>`).
*   Functions to call methods on the trait object.
*   A function to free the memory of the trait object.

**Example FFI layer in the Rust plugin (`my_custom_rust_connector/src/lib.rs`):**
```rust
// ... (struct MyRustSource and impl SourceConnector as above) ...

// #[no_mangle]
// pub extern "C" fn create_source_connector() -> *mut dyn SourceConnector {
//     Box::into_raw(Box::new(MyRustSource::new()))
// }

// // Additional FFI functions would be needed to call connect, read_data, schema, close
// // on the *mut dyn SourceConnector pointer, handling safety and data conversion.
// // This part is complex and requires careful design for memory safety and ergonomics.
// // For example, for read_data, one might need a way to iterate from the C side.

// #[no_mangle]
// pub extern "C" fn destroy_source_connector(ptr: *mut dyn SourceConnector) {
//     if !ptr.is_null() {
//         unsafe { Box::from_raw(ptr); }
//     }
// }

// Similarly for EnrichmentFunction
// #[no_mangle]
// pub extern "C" fn create_enrichment_function() -> *mut dyn EnrichmentFunction {
//     Box::into_raw(Box::new(AddMetadataFunction))
// }
// ... FFI wrappers for process ...
// #[no_mangle]
// pub extern "C" fn destroy_enrichment_function(ptr: *mut dyn EnrichmentFunction) {
//     if !ptr.is_null() {
//         unsafe { Box::from_raw(ptr); }
//     }
// }
```
**Note:** Creating safe and ergonomic FFI wrappers for traits with methods like `read_data` (returning iterators) or methods taking/returning complex types like `serde_json::Value` is non-trivial. It often involves serializing data (e.g., to JSON strings or C-structs) across the FFI boundary.

### 3. Plugin Manager in Main Application
A conceptual `RustPluginManager` in the EKB platform's Rust backend:
```rust
// Conceptual RustPluginManager
// use libloading::{Library, Symbol};
// use std::collections::HashMap;
// use crate::sdk_interfaces::connectors::SourceConnector; // Path to SDK traits
// use crate::sdk_interfaces::functions::EnrichmentFunction;
// use serde_json::Value;

// pub struct RustPluginManager {
//     loaded_libraries: Vec<Library>,
//     source_connectors: HashMap<String, Box<dyn SourceConnector>>, // Store instances
//     enrichment_functions: HashMap<String, Box<dyn EnrichmentFunction>>,
// }

// impl RustPluginManager {
//     pub fn new() -> Self {
//         RustPluginManager {
//             loaded_libraries: Vec::new(),
//             source_connectors: HashMap::new(),
//             enrichment_functions: HashMap::new(),
//         }
//     }

//     pub unsafe fn load_plugin(&mut self, path: &str, plugin_name: &str) -> Result<(), String> {
//         let lib = Library::new(path).map_err(|e| e.to_string())?;
//         self.loaded_libraries.push(lib); // Keep library loaded

//         // Example for a SourceConnector
//         // Assuming a convention for constructor symbol name, e.g., create_<plugin_name>_source_connector
//         let constructor_name = format!("create_{}_source_connector", plugin_name);
//         if let Ok(constructor_sym) = self.loaded_libraries.last().unwrap().get::<unsafe extern "C" fn() -> *mut dyn SourceConnector>(constructor_name.as_bytes()) {
//             let raw_connector = constructor_sym();
//             if !raw_connector.is_null() {
//                 let connector = Box::from_raw(raw_connector);
//                 self.source_connectors.insert(plugin_name.to_string(), connector);
//                 println!("Loaded Rust SourceConnector: {}", plugin_name);
//             }
//         }

//         // Example for an EnrichmentFunction
//         let func_constructor_name = format!("create_{}_enrichment_function", plugin_name);
//          if let Ok(constructor_sym) = self.loaded_libraries.last().unwrap().get::<unsafe extern "C" fn() -> *mut dyn EnrichmentFunction>(func_constructor_name.as_bytes()) {
//             let raw_function = constructor_sym();
//             if !raw_function.is_null() {
//                 let function = Box::from_raw(raw_function);
//                 self.enrichment_functions.insert(plugin_name.to_string(), function);
//                 println!("Loaded Rust EnrichmentFunction: {}", plugin_name);
//             }
//         }
//         Ok(())
//     }
    
//     // Methods to get and use plugins, handling FFI calls to their methods.
//     // This would require more FFI wrapper functions in the plugin itself.
// }
```
This `RustPluginManager` would scan a designated plugin directory, load dynamic libraries, and use the FFI functions to instantiate and interact with the plugin implementations.

### 4. Usage in Data Flows
Similar to Python, flow definitions would reference Rust plugins by name. The Rust execution engine would then use the `RustPluginManager` to invoke them. The data exchange (e.g., `serde_json::Value`) would need to be carefully managed across the FFI boundary (e.g., by serializing to/from JSON strings or using C-compatible representations).

## Packaging
Rust plugins are distributed as compiled dynamic libraries (`.so`, `.dylib`, `.dll`). The EKB platform would need to specify the target architecture for these libraries.

Developing Rust plugins offers performance benefits but involves more complexity in terms of FFI and type safety across the plugin boundary compared to Python's dynamic nature.
