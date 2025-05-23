from abc import ABC, abstractmethod
from typing import Dict, Iterable, Any

class SourceConnector(ABC):
    """
    Abstract Base Class for Source Connector plugins.
    Source Connectors are responsible for fetching data from various external
    or internal systems.
    """

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> None:
        """
        Initializes the connector and establishes any necessary connections
        to the data source using the provided configuration.
        This method is called once when the plugin is loaded or a flow
        utilizing this connector starts.

        Args:
            config: A dictionary containing configuration parameters specific
                    to this connector instance (e.g., API keys, file paths,
                    database connection strings).
        """
        pass

    @abstractmethod
    def read_data(self) -> Iterable[Dict[str, Any]]:
        """
        Reads data from the source and yields it as an iterable of dictionaries.
        Each dictionary represents a single data record.
        This method might be called multiple times if the data source is polled,
        or it can be a generator that yields data records as they become available.

        Returns:
            An iterable of dictionaries, where each dictionary is a data record.
        """
        pass

    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """
        Returns a dictionary representing the schema of the data records
        produced by this connector. This could be a JSON Schema, a dictionary
        of field names to types, or any other structured schema representation
        that the EKB platform can understand.

        Returns:
            A dictionary describing the data schema.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes any open connections and performs necessary cleanup operations.
        This method is called when the plugin is unloaded or a flow utilizing
        this connector finishes its execution.
        """
        pass
# Example usage (for documentation or testing, not part of the interface itself):
# class MyDummyConnector(SourceConnector):
#     def connect(self, config: Dict[str, Any]) -> None: print(f"Connected with {config}")
#     def read_data(self) -> Iterable[Dict[str, Any]]: yield {"data": "dummy"}; yield {"data": "another_dummy"}
#     def schema(self) -> Dict[str, Any]: return {"type": "object", "properties": {"data": {"type": "string"}}}
#     def close(self) -> None: print("Closed")
