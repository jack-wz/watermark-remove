# EKB Platform Plugin SDK

## Overview

The EKB Platform Plugin SDK allows developers to extend the functionality of the Enterprise Knowledge Base (EKB) platform by creating custom plugins. These plugins can integrate new data sources, add data enrichment capabilities, or introduce other custom processing steps into the EKB data pipelines.

The SDK is designed to support plugins written in both Python and Rust, providing language-specific interfaces and guidelines for each.

## Purpose

The primary goals of this SDK are:
*   **Extensibility:** Enable third-party developers or internal teams to add new features without modifying the core EKB platform code.
*   **Standardization:** Provide clear contracts (interfaces/traits) for how plugins should behave and interact with the EKB platform.
*   **Integration:** Facilitate the discovery, loading, and management of plugins by the EKB platform.

## Types of Plugins Supported

The EKB platform primarily supports backend plugins that can be integrated into its data processing and ingestion workflows, such as those managed by a system like CocoIndex or similar orchestration services. Key plugin types include:

1.  **Source Connectors:**
    *   These plugins are responsible for fetching data from various external or internal systems. Examples include connectors for databases, file systems, APIs, message queues, etc.
    *   They handle the initial connection, data retrieval, and potentially provide a schema definition for the data they source.

2.  **Enrichment Functions (Processors):**
    *   These plugins take data (often from a source connector or a previous processing step) and transform or enrich it. Examples include:
        *   Natural Language Processing (NLP) functions (e.g., entity extraction, sentiment analysis, summarization).
        *   Data cleaning and validation functions.
        *   Format conversion functions.
        *   Embedding generation functions.
        *   Calling external APIs to augment data.

3.  **Sink Connectors (Conceptual):**
    *   While not explicitly detailed for interface definition in this initial SDK outline, sink connectors would be responsible for writing processed data to target systems (e.g., databases, search indexes, data warehouses). The SDK might be extended to cover these in the future.

## General Plugin Concepts

### Packaging
Plugins should be packaged according to their language-specific conventions.
*   **Python:** Typically as Python packages (e.g., wheels) that can be installed into the EKB platform's Python environment.
*   **Rust:** Typically as compiled dynamic libraries (`.so`, `.dylib`, `.dll`) or potentially static libraries linked into a custom EKB build.

### Versioning
*   Plugins should follow semantic versioning (SemVer).
*   The EKB platform will need a mechanism to handle plugin versions, potentially specifying compatibility ranges.
*   Plugin interfaces/traits may also be versioned to manage breaking changes.

### Lifecycle Management (Conceptual)
The EKB platform would need a plugin management system responsible for:
*   **Discovery:** Finding available plugins (e.g., from a designated directory, through entry points, or a plugin registry).
*   **Loading:** Dynamically loading plugin code and making it available to the system.
*   **Initialization:** Instantiating plugins and providing them with necessary configuration.
*   **Execution:** Calling plugin methods/functions as part of data processing flows.
*   **Unloading/Updating:** (More advanced) Mechanisms for safely unloading, updating, or disabling plugins.

## Next Steps

For detailed information on developing plugins in a specific language, please refer to:
*   [Python SDK Details](./python_sdk.md)
*   [Rust SDK Details](./rust_sdk.md)
