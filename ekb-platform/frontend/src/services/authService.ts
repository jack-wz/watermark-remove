import axios from 'axios';
import { SignupPayload, LoginPayload } from '../types/auth'; // Assuming types are defined here

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const signup = async (payload: SignupPayload) => {
  try {
    const response = await apiClient.post('/auth/signup', payload);
    return response.data;
  } catch (error: any) {
    throw error.response?.data || { message: 'An unknown error occurred during signup.' };
  }
};

export const login = async (payload: LoginPayload) => {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const formData = new URLSearchParams();
  formData.append('username', payload.username);
  formData.append('password', payload.password);

  try {
    const response = await apiClient.post('/auth/login/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    // Store the token upon successful login
    if (response.data.access_token) {
      localStorage.setItem('accessToken', response.data.access_token);
      // You might want to set the Authorization header for subsequent requests globally here
      // apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
    }
    return response.data;
  } catch (error: any) {
    throw error.response?.data || { message: 'An unknown error occurred during login.' };
  }
};

export const logout = () => {
  localStorage.removeItem('accessToken');
  // Remove Authorization header if it was set globally
  // delete apiClient.defaults.headers.common['Authorization'];
};

export const getCurrentUser = () => {
  // This function would typically make a request to a /users/me endpoint
  // For now, it can just check if a token exists or decode it (client-side decoding is not recommended for sensitive data)
  const token = localStorage.getItem('accessToken');
  if (!token) return null;
  
  // In a real app, you'd call an API endpoint to get user info using the token.
  // Or, if the token contains user info (not recommended to rely solely on this without verification), decode it.
  // For this basic example, we'll just indicate a user is logged in if a token is present.
  // You might decode the token to get username/user_id if they are stored there, but be cautious.
  try {
    // const decoded: { sub: string, user_id: string, exp: number } = jwt_decode(token); // Example if using jwt-decode
    // return { username: decoded.sub, userId: decoded.user_id };
    return { tokenExists: true }; // Simplified
  } catch (error) {
    console.error("Error decoding token:", error);
    return null;
  }
};

// Add other auth-related API calls here, e.g., forgot password, verify email, etc.

// Interceptor to add JWT token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token && config.url !== '/auth/login/token' && config.url !== '/auth/signup') {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
