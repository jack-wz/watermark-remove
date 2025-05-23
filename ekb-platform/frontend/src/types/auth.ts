// Type definitions for authentication payloads and responses

export interface SignupPayload {
  username: string;
  email: string;
  password: string;
  full_name?: string; // Optional full name
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  // Include other user details if your backend sends them on login/signup
  user?: {
    user_id: string;
    username: string;
    email: string;
    full_name?: string;
    is_active: boolean;
  };
}

export interface ErrorResponse {
  detail?: string | { msg: string; type: string }[]; // FastAPI error format
  message?: string; // General message
}

// You can expand this with more specific types as needed
// e.g., for user profiles, different error structures, etc.
