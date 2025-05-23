import axios from 'axios'; // Assuming axios is used as in authService.ts

// Re-use or define API_BASE_URL as in authService.ts
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

// Get the global apiClient instance if it's exported from authService or a similar central place.
// For now, creating a new one or assuming it's configured similarly.
// Ideally, you'd have a single configured Axios instance.
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // No need to set Content-Type: multipart/form-data here,
  // Axios does it automatically when FormData is passed as data.
});

// Interceptor to add JWT token to requests if available (similar to authService)
// This is crucial and should ideally be part of a global Axios setup.
// If not already global, this needs to be added for this service too.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      // Do not set Authorization header for OIDC login/signup related paths if they are handled by this client.
      // For file upload, token is required.
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


export interface IngestionResponse {
  doc_id: string;
  source_uri: string;
  doc_type: string;
  processing_status: string;
  message: string;
  space_id?: string;
  uploaded_by_user_id: string;
  doc_metadata?: Record<string, any>;
  created_at: string; // Assuming ISO date string
}

export interface IngestionErrorResponse {
    detail?: string | { msg: string; type: string }[];
}

// Interface for the backend's IngestedDocumentDisplay schema
export interface IngestedDocumentDisplay {
  doc_id: string; // UUID as string
  source_uri: string;
  doc_type: string;
  extracted_text?: string | null;
  doc_metadata?: Record<string, any> | null;
  space_id?: string | null; // UUID as string
  uploaded_by_user_id?: string | null; // UUID as string
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  processing_status?: string | null;
  last_processed_at?: string | null; // ISO date string
  error_message?: string | null;
}


export const uploadFile = async (file: File, spaceId?: string): Promise<IngestionResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (spaceId) {
    formData.append('space_id', spaceId);
  }

  try {
    // The Content-Type header will be set automatically by Axios to multipart/form-data
    // when it detects FormData as the payload.
    const response = await apiClient.post<IngestionResponse>('/ingestion/upload/file', formData);
    return response.data;
  } catch (error: any) {
    // Handle errors, similar to authService
    if (axios.isAxiosError(error) && error.response) {
      const errorData = error.response.data as IngestionErrorResponse;
      if (typeof errorData.detail === 'string') {
        throw new Error(errorData.detail);
      } else if (Array.isArray(errorData.detail)) {
        throw new Error(errorData.detail.map(e => e.msg).join(', '));
      } else {
        throw new Error(error.message || 'An unknown error occurred during file upload.');
      }
    }
    throw new Error(error.message || 'An unknown error occurred during file upload.');
  }
};

export const getDocumentById = async (docId: string): Promise<IngestedDocumentDisplay> => {
  try {
    const response = await apiClient.get<IngestedDocumentDisplay>(`/ingestion/documents/${docId}`);
    return response.data;
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response) {
      const errorData = error.response.data as SearchErrorResponse; // Can reuse SearchErrorResponse if detail structure is same
      if (typeof errorData.detail === 'string') {
        throw new Error(errorData.detail);
      } else if (Array.isArray(errorData.detail)) {
        throw new Error(errorData.detail.map(e => e.msg).join(', '));
      } else {
        throw new Error(error.message || 'An unknown error occurred while fetching the document.');
      }
    }
    throw new Error(error.message || 'An unknown error occurred while fetching the document.');
  }
};
