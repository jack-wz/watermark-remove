import React, { useState, ChangeEvent, FormEvent } from 'react';
import { uploadFile, IngestionResponse, IngestionErrorResponse } from '../../services/ingestionService';

const FileUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [spaceId, setSpaceId] = useState<string>(''); // For optional space_id input
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setSuccessMessage(null); // Clear previous messages
      setErrorMessage(null);
    }
  };

  const handleSpaceIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSpaceId(event.target.value);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select a file to upload.');
      return;
    }

    setIsLoading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const response: IngestionResponse = await uploadFile(selectedFile, spaceId || undefined);
      setSuccessMessage(
        `File uploaded successfully! Document ID: ${response.doc_id}. Status: ${response.processing_status}. URI: ${response.source_uri}`
      );
      setSelectedFile(null); // Clear the file input
      setSpaceId(''); // Clear spaceId input
      // Clear the actual file input element (if needed, by resetting the form or input value)
      const fileInput = document.getElementById('fileInput') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (error: any) {
      // The error should be an instance of Error with a message from the service
      setErrorMessage(error.message || 'File upload failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2>Upload Markdown Document</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="fileInput">Choose Markdown file (.md, .markdown):</label>
          <input
            type="file"
            id="fileInput"
            accept=".md,.markdown"
            onChange={handleFileChange}
          />
        </div>
        <div style={{ marginTop: '10px' }}>
          <label htmlFor="spaceIdInput">Space ID (Optional):</label>
          <input
            type="text"
            id="spaceIdInput"
            value={spaceId}
            onChange={handleSpaceIdChange}
            placeholder="Enter Space ID (UUID)"
          />
        </div>
        <div style={{ marginTop: '20px' }}>
          <button type="submit" disabled={isLoading || !selectedFile}>
            {isLoading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>
      </form>
      {successMessage && (
        <p style={{ color: 'green', marginTop: '10px' }}>{successMessage}</p>
      )}
      {errorMessage && (
        <p style={{ color: 'red', marginTop: '10px' }}>{errorMessage}</p>
      )}
    </div>
  );
};

export default FileUpload;
