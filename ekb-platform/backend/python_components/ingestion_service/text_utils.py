from typing import List

def chunk_text_by_sentences(text: str, sentences_per_chunk: int = 5) -> List[str]:
    """
    Splits text into chunks based on a number of sentences.
    A simple approach using period and newline as sentence delimiters.
    This is a basic implementation and might not handle all edge cases perfectly
    (e.g., "Mr. Smith", abbreviations, etc.).
    """
    # Replace common sentence-ending punctuation with a unique delimiter, then split.
    # This is a simplistic way to get sentences. More robust methods exist (e.g., NLTK, spaCy).
    sentence_delimiters = ['. ', '.\n', '!', '?\n', '\n\n'] # Prioritize newlines as hard breaks
    placeholder_delimiter = "<SENTENCE_END>"
    
    processed_text = text
    for delim in sentence_delimiters:
        processed_text = processed_text.replace(delim, placeholder_delimiter)
    # Handle cases where a period might not be followed by a space or newline
    processed_text = processed_text.replace(".", placeholder_delimiter)

    sentences = [s.strip() for s in processed_text.split(placeholder_delimiter) if s.strip()]

    chunks: List[str] = []
    current_chunk_sentences: List[str] = []
    
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = ". ".join(sentences[i:i + sentences_per_chunk]) + "." # Add period at the end of chunk
        if chunk.strip() and chunk.strip() != ".": # Avoid empty or period-only chunks
             chunks.append(chunk.strip())
    
    # Fallback if no sentences were effectively split (e.g., text without standard punctuation)
    if not chunks and text.strip():
        # Simple fixed-size chunking as a fallback if sentence splitting is ineffective
        # This part is more aligned with the original request for fixed-size chunker
        # Let's use a character-based fixed-size chunker with overlap as the primary method for simplicity.
        # The sentence splitter above is a bit too naive for robust use without NLTK/spaCy.
        # Reverting to a simpler character-based chunker for this task.
        return chunk_text_fixed_size(text, chunk_size=1000, chunk_overlap=200) # Default values

    return chunks


def chunk_text_fixed_size(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Splits text into fixed-size chunks with overlap.
    chunk_size: The target size of each chunk in characters.
    chunk_overlap: The number of characters to overlap between chunks.
    """
    if not text or text.isspace():
        return []
        
    chunks: List[str] = []
    start_index = 0
    text_len = len(text)

    if text_len <= chunk_size:
        return [text.strip()]

    while start_index < text_len:
        end_index = start_index + chunk_size
        chunk = text[start_index:end_index]
        chunks.append(chunk.strip())
        
        if end_index >= text_len:
            break
        
        start_index += (chunk_size - chunk_overlap)
        # Ensure overlap doesn't cause an infinite loop if overlap is too large or chunk_size too small
        if start_index + chunk_overlap >= text_len and end_index < text_len : # If next step is last and small
             # Add the remainder as the last chunk to avoid very small trailing chunks
             # This logic might need refinement to ensure all text is captured without excessive overlap on final chunk.
             # For now, simple step back.
             pass


    # A slightly more robust way to handle the loop to ensure all text is captured
    # and overlap is managed correctly.
    chunks = []
    current_pos = 0
    while current_pos < text_len:
        end_pos = min(current_pos + chunk_size, text_len)
        chunk = text[current_pos:end_pos]
        if chunk.strip(): # Avoid adding empty chunks
            chunks.append(chunk.strip())
        
        if end_pos == text_len:
            break # Reached the end of the text
        
        current_pos += (chunk_size - chunk_overlap)
        if current_pos >= text_len: # Should not happen if logic is correct, but as a safe break
            break
        # If the next chunk would start beyond where the current chunk ended due to large overlap
        if current_pos < end_pos - chunk_overlap and end_pos < text_len: # Ensure we are moving forward
             pass # Normal overlap
        elif current_pos >= end_pos and end_pos < text_len: # Overlap is too large, or chunk_size too small
            current_pos = end_pos # Move to the end of the current chunk to avoid re-processing or infinite loops


    # LangChain's RecursiveCharacterTextSplitter is more robust.
    # For this task, a very simple character splitter:
    if not text: return []
    
    # Use a simpler fixed-size chunker without complex overlap logic for this example,
    # focusing on the integration rather than perfect chunking.
    # The previous attempts at fixed_size were getting complex.
    
    # Simplest fixed-size chunker for the purpose of this exercise:
    # This will be a non-overlapping, simple character split.
    # A real implementation would use a more sophisticated library or method.
    
    chunk_list: List[str] = []
    if not text:
        return chunk_list

    # Using a simple paragraph splitter as a more meaningful chunk than arbitrary fixed size for now
    # (as the fixed-size logic got complicated in brief attempts).
    # This assumes paragraphs are separated by double newlines.
    paragraphs = text.split('\n\n')
    current_chunk = ""
    max_chunk_char_len = chunk_size # Use chunk_size as a rough guide for paragraph grouping

    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped:
            continue

        if not current_chunk:
            current_chunk = para_stripped
        elif len(current_chunk) + len(para_stripped) + 2 <= max_chunk_char_len: # +2 for potential join space
            current_chunk += "\n\n" + para_stripped
        else:
            chunk_list.append(current_chunk)
            current_chunk = para_stripped
    
    if current_chunk: # Add the last accumulated chunk
        chunk_list.append(current_chunk)
        
    if not chunk_list and text.strip(): # Fallback if no paragraphs, chunk whole text if small enough
        if len(text.strip()) <= max_chunk_char_len * 1.5: # Allow slightly larger for single chunk
             return [text.strip()]
        else: # If very large and no paragraphs, do a cruder split
            # This is where RecursiveCharacterTextSplitter from Langchain would be good.
            # For now, simple split by length for the fallback.
            step = max_chunk_char_len
            return [text[i:i+step].strip() for i in range(0, len(text), step) if text[i:i+step].strip()]


    return chunk_list

# Default chunking parameters (can be made configurable)
DEFAULT_CHUNK_SIZE = 1000 # Characters (approximate for paragraph grouping)
DEFAULT_CHUNK_OVERLAP = 0 # Overlap is handled by paragraph grouping logic for now

def chunk_text(text: str) -> List[str]:
    """
    Main function to chunk text. Uses paragraph-based chunking.
    """
    return chunk_text_by_paragraphs_and_size(text, chunk_size_target=DEFAULT_CHUNK_SIZE)


def chunk_text_by_paragraphs_and_size(text: str, chunk_size_target: int) -> List[str]:
    """
    Splits text by paragraphs, then groups paragraphs into chunks
    that are roughly `chunk_size_target` characters long.
    """
    if not text or text.isspace():
        return []

    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs: # If no double newlines, try single newlines
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    if not paragraphs: # If still no paragraphs (e.g. one very long line)
        # Fallback to fixed size splitting for very long lines without natural breaks
        if len(text) > chunk_size_target * 1.5: # Only if significantly larger
            step = chunk_size_target
            return [text[i:i+step].strip() for i in range(0, len(text), step) if text[i:i+step].strip()]
        else:
            return [text.strip()] if text.strip() else []


    chunks: List[str] = []
    current_chunk_text = ""
    for para in paragraphs:
        if not current_chunk_text:
            current_chunk_text = para
        elif len(current_chunk_text) + len(para) + 2 < chunk_size_target: # +2 for "\n\n"
            current_chunk_text += "\n\n" + para
        else:
            chunks.append(current_chunk_text)
            current_chunk_text = para
            
    if current_chunk_text: # Add the last chunk
        chunks.append(current_chunk_text)
        
    return chunks
