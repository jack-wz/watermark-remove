import React, { useState, FormEvent } from 'react';
import { semanticSearch, SearchResultItem } from '../../services/searchService';
import { getDocumentById, IngestedDocumentDisplay } from '../../services/ingestionService'; // Import getDocumentById
import MarkdownViewer from '../Viewer/MarkdownViewer'; // Import MarkdownViewer
// Radix UI components can be imported here if desired for styling, e.g.:
// import { TextField, Button, Box, Card, Text, Flex, Heading, Dialog } from '@radix-ui/themes';

// Basic Modal Style (can be improved or replaced with a library like Radix Dialog)
const modalOverlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalContentStyle: React.CSSProperties = {
  backgroundColor: 'white',
  padding: '20px',
  borderRadius: '8px',
  maxWidth: '80%',
  maxHeight: '80vh',
  overflowY: 'auto',
  position: 'relative', // For close button positioning
};

const modalCloseButtonStyle: React.CSSProperties = {
  position: 'absolute',
  top: '10px',
  right: '10px',
  background: 'none',
  border: 'none',
  fontSize: '1.5rem',
  cursor: 'pointer',
};


const SearchPage: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [topK, setTopK] = useState<number>(10);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedQuery, setSearchedQuery] = useState<string | null>(null);

  // State for Markdown Viewer Modal
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedDocContent, setSelectedDocContent] = useState<string | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);
  const [isLoadingDoc, setIsLoadingDoc] = useState<boolean>(false);

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) {
      setError('Please enter a search query.');
      setResults([]);
      setSearchedQuery(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults([]);
    setSearchedQuery(query); // Store the query that was searched

    try {
      const response = await semanticSearch(query, topK);
      setResults(response.results);
      if (response.results.length === 0) {
        setError('No results found for your query.');
      }
    } catch (err: any) {
      // The error should be an instance of Error with a message from the service
      setError(err.message || 'An unknown error occurred during search.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDocument = async (docId: string) => {
    setIsLoadingDoc(true);
    setModalError(null);
    setSelectedDocContent(null);
    setIsModalOpen(true); // Open modal to show loading state

    try {
      const document: IngestedDocumentDisplay = await getDocumentById(docId);
      setSelectedDocContent(document.extracted_text || 'No text content available for this document.');
    } catch (err: any) {
      setModalError(err.message || 'Failed to fetch document content.');
    } finally {
      setIsLoadingDoc(false);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedDocContent(null);
    setModalError(null);
  };


  return (
    <div>
      <h2>Semantic Search</h2>
      <form onSubmit={handleSearch}>
        <div>
          <label htmlFor="searchQuery" style={{ marginRight: '10px' }}>Search Query:</label>
          <input
            type="text"
            id="searchQuery"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query"
            style={{ minWidth: '300px', padding: '8px' }}
          />
        </div>
        <div style={{ marginTop: '10px' }}>
          <label htmlFor="topK" style={{ marginRight: '10px' }}>Top K:</label>
          <input
            type="number"
            id="topK"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value, 10))}
            min="1"
            max="100"
            style={{ padding: '8px', width: '80px' }}
          />
        </div>
        <div style={{ marginTop: '20px' }}>
          <button type="submit" disabled={isLoading} style={{ padding: '10px 15px' }}>
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <p style={{ color: 'red', marginTop: '20px' }}>{error}</p>
      )}

      {searchedQuery && !isLoading && (
        <div style={{ marginTop: '30px' }}>
          <h3>Results for: "{searchedQuery}"</h3>
          {results.length > 0 ? (
            <ul style={{ listStyleType: 'none', padding: 0 }}>
              {results.map((item) => (
                <li key={item.chunk_id} style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '10px', borderRadius: '5px' }}>
                  <p style={{ fontSize: '0.9em', color: '#555' }}>
                    Source: {item.source_uri} (Doc ID: {item.doc_id})
                  </p>
                  <p style={{ fontWeight: 'bold', marginBottom: '5px' }}>{item.chunk_text}</p>
                  <p style={{ fontSize: '0.9em', color: '#333' }}>
                    Similarity Score: {item.similarity_score.toFixed(4)} 
                    (L2 distance, smaller is better)
                  </p>
                  {item.doc_metadata && (
                    <details style={{ marginTop: '5px', fontSize: '0.85em' }}>
                      <summary>Document Metadata</summary>
                      <pre style={{ backgroundColor: '#f5f5f5', padding: '5px', borderRadius: '3px' }}>
                        {JSON.stringify(item.doc_metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                  <button 
                    onClick={() => handleViewDocument(item.doc_id)} 
                    style={{ marginTop: '10px', padding: '5px 10px' }}
                    disabled={isLoadingDoc && selectedDocContent === null} // Disable if currently loading this or another doc
                  >
                    {isLoadingDoc && selectedDocContent === null ? 'Loading Doc...' : 'View Full Document'}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      )}

      {isModalOpen && (
        <div style={modalOverlayStyle} onClick={closeModal}>
          <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}> {/* Prevents modal close on content click */}
            <button style={modalCloseButtonStyle} onClick={closeModal}>&times;</button>
            {isLoadingDoc && <p>Loading document content...</p>}
            {modalError && <p style={{ color: 'red' }}>Error: {modalError}</p>}
            {selectedDocContent && !isLoadingDoc && !modalError && (
              <MarkdownViewer markdownContent={selectedDocContent} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
