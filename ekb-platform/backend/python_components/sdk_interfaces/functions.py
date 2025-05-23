from abc import ABC, abstractmethod
from typing import Dict, Any

class EnrichmentFunction(ABC):
    """
    Abstract Base Class for Enrichment Function plugins.
    Enrichment Functions take a single data record (as a dictionary)
    and return an enriched or transformed version of it. They can be used
    for tasks like data cleaning, NLP processing, or adding new fields
    based on existing data.
    """

    @abstractmethod
    def process(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single data record and returns the modified record.

        Args:
            data: A dictionary representing the input data record.
            config: A dictionary containing configuration parameters specific
                    to this function's operation. This allows for runtime
                    customization of the enrichment logic (e.g., specifying
                    which field to analyze, API keys for external services, etc.).

        Returns:
            A dictionary representing the processed (enriched or transformed)
            data record. The function can modify the input 'data' in-place
            and return it, or create and return a new dictionary.
        """
        pass

# Example usage (for documentation or testing):
# class MyDummyFunction(EnrichmentFunction):
#     def process(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
#         data["processed_by"] = config.get("processor_name", "MyDummyFunction")
#         data["original_keys"] = list(data.keys())
#         return data
