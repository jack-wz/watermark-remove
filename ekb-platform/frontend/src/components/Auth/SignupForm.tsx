import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'; // For redirection
import { signup } from '../../services/authService';
import { SignupPayload, ErrorResponse } from '../../types/auth';

const SignupForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const validateEmail = (email: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!username || !email || !password) {
      setError('Username, email, and password are required.');
      return;
    }
    if (!validateEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    const payload: SignupPayload = { username, email, password, full_name: fullName || undefined };

    try {
      await signup(payload);
      setSuccessMessage('Signup successful! Please proceed to login.');
      // Optionally redirect to login page after a delay or directly
      setTimeout(() => navigate('/login'), 2000); 
    } catch (err: any) {
      const errorData = err as ErrorResponse;
      if (typeof errorData.detail === 'string') {
        setError(errorData.detail);
      } else if (Array.isArray(errorData.detail)) {
        setError(errorData.detail.map(e => e.msg).join(', '));
      } else if (errorData.message) {
        setError(errorData.message);
      } else {
        setError('An unknown error occurred during signup.');
      }
    }
  };

  return (
    <div>
      <h2>Signup</h2>
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
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
            minLength={8}
          />
        </div>
        <div>
          <label htmlFor="fullName">Full Name (Optional):</label>
          <input
            type="text"
            id="fullName"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
        <button type="submit">Signup</button>
      </form>
    </div>
  );
};

export default SignupForm;
