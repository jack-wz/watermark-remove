#!/usr/bin/env python3

import argparse
import os
import sys

# Add project root to sys.path to allow finding the watermark_remover package
# This assumes the script is in watermark_remover_project/scripts/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from watermark_remover.core.lama_wrapper import LaMaWrapper

def main():
    """
    Main function to handle CLI arguments and process the image.
    """
    parser = argparse.ArgumentParser(description="Remove watermark from a single image using LaMa (placeholder).")
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Path to the input image with watermark."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Path to save the processed image."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Optional path to the LaMa model. (Currently ignored by placeholder)"
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input image not found at {args.input}")
        sys.exit(1)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir: # If output_dir is not empty (i.e., not saving in current dir)
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        print(f"Initializing LaMaWrapper (model: {args.model_path if args.model_path else 'default/placeholder'})...")
        lama_wrapper = LaMaWrapper(model_path=args.model_path)
        
        print(f"Processing image: {args.input} -> {args.output}")
        processed_path = lama_wrapper.remove_watermark(args.input, args.output)
        
        print(f"Successfully processed image. Output saved to: {processed_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```
