import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../../services/authService';
import { LoginPayload, ErrorResponse, AuthResponse } from '../../types/auth';

const LoginForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!username || !password) {
      setError('Username and password are required.');
      return;
    }

    const payload: LoginPayload = { username, password };

    try {
      const response: AuthResponse = await login(payload);
      // Assuming login service stores the token in localStorage
      if (response.access_token) {
        // Optionally, you can store user details or redirect based on roles later
        // For now, just redirect to a placeholder dashboard
        navigate('/dashboard'); 
      } else {
        setError('Login failed: No access token received.');
      }
    } catch (err: any) {
      const errorData = err as ErrorResponse;
       if (typeof errorData.detail === 'string') {
        setError(errorData.detail);
      } else if (Array.isArray(errorData.detail)) {
        setError(errorData.detail.map(e => e.msg).join(', '));
      } else if (errorData.message) {
        setError(errorData.message);
      } else {
        setError('An unknown error occurred during login.');
      }
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Username:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">Login</button>
      </form>
      <hr />
      <button onClick={handleOidcLogin} style={{ marginTop: '10px' }}>
        Login with SSO / OIDC
      </button>
    </div>
  );

  function handleOidcLogin() {
    // Redirect to the backend's OIDC login initiation endpoint
    // Ensure this URL matches your backend configuration
    window.location.href = 'http://localhost:8000/api/v1/auth/oidc/login';
  }
};

export default LoginForm;
