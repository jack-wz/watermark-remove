import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
// Assuming getCurrentUser from authService can be adapted or a new function is made
// to fetch user details after setting the token. For now, we'll focus on token storage.
// import { getCurrentUser } from '../../services/authService'; 

const OidcCallback: React.FC = () => {
  const [message, setMessage] = useState('Processing OIDC login...');
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const token = queryParams.get('token'); // Assuming backend redirects with ?token=<jwt_token>

    if (token) {
      localStorage.setItem('accessToken', token);
      setMessage('Login successful! Redirecting to dashboard...');
      
      // Optional: Fetch user details immediately after setting token
      // This would typically involve calling a '/users/me' endpoint
      // For example:
      // const fetchUser = async () => {
      //   try {
      //     // await getCurrentUser(); // This function might need to be adapted or use a global state for user
      //     navigate('/dashboard');
      //   } catch (error) {
      //     setMessage('Failed to fetch user details after OIDC login. Please try logging in again.');
      //     localStorage.removeItem('accessToken'); // Clean up token if user fetch fails
      //     setTimeout(() => navigate('/login'), 3000);
      //   }
      // };
      // fetchUser();
      
      // For now, directly navigate to dashboard after setting token
      setTimeout(() => navigate('/dashboard'), 1500);

    } else {
      const errorParam = queryParams.get('error');
      const errorDescription = queryParams.get('error_description');
      if (errorParam) {
        setMessage(`OIDC Login Error: ${errorParam} - ${errorDescription || 'No description provided.'}`);
      } else {
        setMessage('OIDC login failed: No token received. Please try again.');
      }
      setTimeout(() => navigate('/login'), 3000);
    }
  }, [location, navigate]);

  return (
    <div>
      <h2>OIDC Login Callback</h2>
      <p>{message}</p>
    </div>
  );
};

export default OidcCallback;
