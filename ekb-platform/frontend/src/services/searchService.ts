import axios from 'axios'; // Assuming axios is used as in authService.ts

// Re-use or define API_BASE_URL as in authService.ts or a central config
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

// Assuming a global Axios instance is configured with interceptors (like in authService.ts)
// If not, apiClient needs to be created and configured here similarly to include the JWT token.
// For this example, let's assume 'apiClient' is exported from a central place or configured globally.
// If authService.ts exports its configured apiClient, that would be ideal.
// For now, creating one for clarity, but in a real app, share the instance.
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// This interceptor should ideally be part of a global Axios setup to avoid duplication.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interfaces mirroring backend Pydantic schemas for search
export interface SearchQueryRequest {
  query_text: string;
  top_k?: number;
}

export interface SearchResultItem {
  doc_id: string; // Assuming UUID is string
  chunk_id: string; // Assuming UUID is string
  chunk_text: string;
  source_uri: string;
  doc_metadata?: Record<string, any>;
  similarity_score: number;
}

export interface SearchResponse {
  query_text: string;
  results: SearchResultItem[];
}

// Error response interface (can be shared or defined per service)
export interface SearchErrorResponse {
    detail?: string | { msg: string; type: string }[];
}

export const semanticSearch = async (queryText: string, topK?: number): Promise<SearchResponse> => {
  const payload: SearchQueryRequest = { query_text: queryText };
  if (topK !== undefined) {
    payload.top_k = topK;
  }

  try {
    const response = await apiClient.post<SearchResponse>('/search/semantic', payload, {
      headers: {
        'Content-Type': 'application/json', // Explicitly set for POST with JSON body
      },
    });
    return response.data;
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response) {
      const errorData = error.response.data as SearchErrorResponse;
      if (typeof errorData.detail === 'string') {
        throw new Error(errorData.detail);
      } else if (Array.isArray(errorData.detail)) {
        throw new Error(errorData.detail.map(e => e.msg).join(', '));
      } else {
        throw new Error(error.message || 'An unknown error occurred during semantic search.');
      }
    }
    throw new Error(error.message || 'An unknown error occurred during semantic search.');
  }
};
