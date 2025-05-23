import React, { ReactNode } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import SignupForm from './components/Auth/SignupForm';
import LoginForm from './components/Auth/LoginForm';
import OidcCallback from './components/Auth/OidcCallback';
import FileUpload from './components/Ingestion/FileUpload';
import SearchPage from './components/Search/SearchPage'; // Import SearchPage

// Simple ProtectedRoute HOC (Higher Order Component)
interface ProtectedRouteProps {
  children: ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    // User not authenticated, redirect to login page
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>; // Render children if authenticated
};


// Placeholder Dashboard component (can now assume user is authenticated if rendered via ProtectedRoute)
const Dashboard: React.FC = () => {
  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome! You are logged in.</p>
      <button onClick={() => {
        localStorage.removeItem('accessToken');
        window.location.href = '/login'; 
      }}>Logout</button>
    </div>
  );
};

// Home component
const Home: React.FC = () => (
  <div>
    <h1>Enterprise Knowledge Base Platform</h1>
    <p>Please login or signup to continue.</p>
  </div>
);

function App() {
  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/signup">Signup</Link>
            </li>
            <li>
              <Link to="/login">Login</Link>
            </li>
            <li>
              <Link to="/dashboard">Dashboard</Link>
            </li>
            <li>
              <Link to="/upload">Upload Document</Link>
            </li>
            <li>
              <Link to="/search">Search Documents</Link> {/* Add Search link */}
            </li>
          </ul>
        </nav>

        <hr />

        <Routes>
          <Route path="/signup" element={<SignupForm />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/oidc-callback" element={<OidcCallback />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/upload" 
            element={
              <ProtectedRoute>
                <FileUpload />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/search" 
            element={
              <ProtectedRoute>
                <SearchPage />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Home />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
