# EKB Platform - Python Plugin SDK

This document provides details for developing backend plugins for the EKB Platform using Python. Python plugins are ideal for data processing, I/O bound tasks, and leveraging the rich Python ecosystem for NLP and data science.

## Interfaces

Python plugins implement predefined Abstract Base Classes (ABCs) to ensure compatibility with the EKB platform. These interfaces are defined in the `ekb_platform.backend.python_components.sdk_interfaces` module (conceptually).

### 1. SourceConnector

A `SourceConnector` plugin is responsible for fetching data from an external or internal source.

**Interface Definition (Conceptual - in `sdk_interfaces/connectors.py`):**
```python
from abc import ABC, abstractmethod
from typing import Dict, Iterable

class SourceConnector(ABC):
    @abstractmethod
    def connect(self, config: Dict) -> None:
        """
        Initializes the connector and establishes any necessary connections
        to the data source using the provided configuration.
        Called once when the plugin is loaded or a flow starts.
        """
        pass

    @abstractmethod
    def read_data(self) -> Iterable[Dict]:
        """
        Reads data from the source and yields it as an iterable of dictionaries.
        Each dictionary represents a single data record.
        This method might be called multiple times or be a generator.
        """
        pass

    @abstractmethod
    def schema(self) -> Dict:
        """
        Returns a dictionary representing the schema of the data records
        produced by this connector. This could be a JSON Schema or similar.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes any open connections and performs cleanup.
        Called when the plugin is unloaded or a flow finishes.
        """
        pass
```

**Implementation Example:**
A developer would create a new Python class that inherits from `SourceConnector` and implements all abstract methods.
```python
# Example: my_custom_connector.py
from ekb_platform.backend.python_components.sdk_interfaces.connectors import SourceConnector
from typing import Dict, Iterable

class MyCustomSource(SourceConnector):
    def __init__(self):
        self._connection = None
        self._config = None

    def connect(self, config: Dict) -> None:
        print(f"Connecting to custom source with config: {config}")
        self._config = config
        # self._connection = ... establish connection ...
        self.is_connected = True # Example state

    def read_data(self) -> Iterable[Dict]:
        if not self.is_connected:
            raise ConnectionError("Not connected to source.")
        # Example: Read data from a CSV file specified in config
        # file_path = self._config.get("file_path")
        # with open(file_path, 'r') as f:
        #     reader = csv.DictReader(f)
        #     for row in reader:
        #         yield row
        yield {"id": 1, "data": "example_data_1"}
        yield {"id": 2, "data": "example_data_2"}

    def schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "data": {"type": "string"}
            }
        }

    def close(self) -> None:
        print("Closing custom source connection.")
        # if self._connection:
        #     self._connection.close()
        self.is_connected = False
```

### 2. EnrichmentFunction

An `EnrichmentFunction` plugin takes a single data record (as a dictionary) and returns an enriched or transformed version of it.

**Interface Definition (Conceptual - in `sdk_interfaces/functions.py`):**
```python
from abc import ABC, abstractmethod
from typing import Dict

class EnrichmentFunction(ABC):
    @abstractmethod
    def process(self, data: Dict, config: Dict) -> Dict:
        """
        Processes a single data record and returns the modified record.
        'config' can provide parameters specific to this function's operation.
        """
        pass
```

**Implementation Example:**
```python
# Example: my_enrichment_plugins.py
from ekb_platform.backend.python_components.sdk_interfaces.functions import EnrichmentFunction
from typing import Dict

class AddTimestampFunction(EnrichmentFunction):
    def process(self, data: Dict, config: Dict) -> Dict:
        import datetime
        data["_enriched_at"] = datetime.datetime.utcnow().isoformat()
        return data

class SentimentAnalyzerFunction(EnrichmentFunction):
    def __init__(self):
        # Potentially load models or resources here if needed once
        # from some_nlp_library import sentiment_model
        # self.model = sentiment_model.load()
        pass

    def process(self, data: Dict, config: Dict) -> Dict:
        text_field = config.get("text_field_to_analyze", "text")
        if text_field in data and isinstance(data[text_field], str):
            # sentiment = self.model.predict(data[text_field])
            sentiment = "positive" # Placeholder
            data["sentiment"] = sentiment
        return data
```

## Plugin Discovery and Loading

The EKB platform needs a mechanism to discover and load these Python plugins.

### 1. Discovery

Conceptual mechanisms for plugin discovery:

*   **Entry Points:**
    *   Plugins can define entry points in their `pyproject.toml` (or `setup.py`). For example, under a group like `ekb_platform.plugins`.
    *   The main application would use `importlib.metadata.entry_points()` to find registered plugins.
    *   **Example `pyproject.toml` for a plugin:**
        ```toml
        [project.entry-points."ekb_platform.plugins"]
        my_custom_source = "my_plugin_package.my_custom_connector:MyCustomSource"
        add_timestamp = "my_plugin_package.my_enrichment_plugins:AddTimestampFunction"
        ```

*   **Directory-Based:**
    *   Plugins are placed in a designated directory (e.g., `ekb-platform/plugins/python/`).
    *   The main application scans this directory for Python modules or packages that adhere to certain naming conventions or contain specific markers (e.g., a `plugin_info.json` file).
    *   Each discovered module would be imported, and classes inheriting from `SourceConnector` or `EnrichmentFunction` would be registered.

### 2. Loading and Registration

A conceptual `PluginManager` in the EKB platform would:
*   **Scan for Plugins:** Use one of the discovery mechanisms.
*   **Validate Plugins:** Check if discovered classes correctly implement the required interfaces.
*   **Register Plugins:** Store references to valid plugin classes, possibly indexed by a unique name (e.g., `my_custom_source`).
    ```python
    # Conceptual PluginManager
    class PluginManager:
        def __init__(self):
            self.source_connectors = {}
            self.enrichment_functions = {}

        def load_plugins(self):
            # Example using entry points
            # from importlib.metadata import entry_points
            # discovered_plugins = entry_points(group='ekb_platform.plugins')
            # for plugin_entry in discovered_plugins:
            #     plugin_class = plugin_entry.load()
            #     if issubclass(plugin_class, SourceConnector):
            #         self.source_connectors[plugin_entry.name] = plugin_class
            #     elif issubclass(plugin_class, EnrichmentFunction):
            #         self.enrichment_functions[plugin_entry.name] = plugin_class
            pass # Actual loading logic

        def get_source_connector(self, name: str, config: Dict) -> SourceConnector:
            # connector_class = self.source_connectors.get(name)
            # if connector_class:
            #     instance = connector_class()
            #     instance.connect(config)
            #     return instance
            # raise ValueError(f"Source connector '{name}' not found.")
            pass

        def get_enrichment_function(self, name: str) -> EnrichmentFunction:
            # function_class = self.enrichment_functions.get(name)
            # if function_class:
            #     return function_class() # Assuming functions might be stateless or manage own state
            # raise ValueError(f"Enrichment function '{name}' not found.")
            pass
    ```

### 3. Usage in Data Flows (e.g., CocoIndex)

A data processing flow definition (like those for CocoIndex) would reference these plugins by their registered names.
```yaml
# Conceptual flow definition snippet
# ...
steps:
  - name: "fetch_data_from_custom_source"
    connector_type: "python_source_connector" # Hint for the platform
    name: "my_custom_source" # Registered name of the Python plugin
    config:
      file_path: "/data/my_input.csv"
      # other config for MyCustomSource

  - name: "add_processing_timestamp"
    processor_type: "python_enrichment_function"
    name: "add_timestamp" # Registered name
    config: {} # No specific config for this simple function

  - name: "analyze_sentiment"
    processor_type: "python_enrichment_function"
    name: "sentiment_analyzer" # Assuming registered name
    config:
      text_field_to_analyze: "customer_review_text"
# ...
```
The EKB platform's flow execution engine would use the `PluginManager` to instantiate and call the appropriate methods of the Python plugins based on such definitions.

## Packaging

Python plugins should be packaged as standard Python distributions (e.g., wheels). This allows them to be installed into the EKB platform's Python environment using `pip`. Dependencies of the plugin should be declared in its `pyproject.toml` or `setup.py`.

This SDK provides a flexible way to extend the EKB platform with custom Python logic for data ingestion and processing.Okay, I've created the `ekb-platform/docs/sdk/README.md` in a previous turn. Now I'll create `python_sdk.md`.
