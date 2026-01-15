import React, { useState, useEffect } from 'react';
import './App.css';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import QuestionInput from './components/QuestionInput';
import ObjectListEditor from './components/ObjectListEditor';
import AnswerDisplay from './components/AnswerDisplay';
import ErrorMessage from './components/ErrorMessage';
import apiClient from './services/apiClient';

type AuthView = 'login' | 'register';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authView, setAuthView] = useState<AuthView>('login');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Main interface state
  const [answer, setAnswer] = useState<string | null>(null);
  const [isQueryLoading, setIsQueryLoading] = useState(false);
  const [isObjectListLoading, setIsObjectListLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [objectListError, setObjectListError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is already authenticated
    setIsAuthenticated(apiClient.isAuthenticated());
  }, []);

  const handleLogin = async (username: string, password: string) => {
    setAuthError(null);
    try {
      await apiClient.login(username, password);
      setIsAuthenticated(true);
      setSuccessMessage('');
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
      throw err;
    }
  };

  const handleRegister = async (username: string, password: string) => {
    setAuthError(null);
    try {
      await apiClient.register(username, password);
      setSuccessMessage('Registration successful! Please login.');
      setAuthView('login');
    } catch (err: any) {
      setAuthError(err.message || 'Registration failed');
      throw err;
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    setIsAuthenticated(false);
    setAuthView('login');
    setSuccessMessage('');
    // Reset main interface state
    setAnswer(null);
    setQueryError(null);
    setObjectListError(null);
    setAuthError(null);
  };

  const handleQuestionSubmit = async (question: string) => {
    setIsQueryLoading(true);
    setQueryError(null);
    setAnswer(null);

    try {
      const response = await apiClient.query(question);
      setAnswer(response.answer);
    } catch (err: any) {
      setQueryError(err.message || 'Failed to get answer');
    } finally {
      setIsQueryLoading(false);
    }
  };

  const handleObjectListUpdate = async (objects: any[]) => {
    setIsObjectListLoading(true);
    setObjectListError(null);
    try {
      await apiClient.updateObjectList(objects);
    } catch (err: any) {
      setObjectListError(err.message || 'Failed to update object list');
      throw err;
    } finally {
      setIsObjectListLoading(false);
    }
  };

  const handleObjectListFetch = async () => {
    try {
      const response = await apiClient.getObjectList();
      return {
        objects: response.objects || [],
        created_at: response.created_at,
        updated_at: response.updated_at
      };
    } catch (err: any) {
      console.error('Failed to fetch object list:', err);
      return { objects: [] };
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="App">
        {successMessage && (
          <div className="success-banner">{successMessage}</div>
        )}
        {authError && (
          <ErrorMessage 
            error={authError} 
            onDismiss={() => setAuthError(null)} 
          />
        )}
        {authView === 'login' ? (
          <LoginForm
            onLogin={handleLogin}
            onSwitchToRegister={() => {
              setAuthView('register');
              setSuccessMessage('');
              setAuthError(null);
            }}
          />
        ) : (
          <RegisterForm
            onRegister={handleRegister}
            onSwitchToLogin={() => {
              setAuthView('login');
              setSuccessMessage('');
              setAuthError(null);
            }}
          />
        )}
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Hybrid RAG Q&A System</h1>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </header>
      <main className="App-main">
        <div className="main-grid">
          <div className="left-column">
            <QuestionInput 
              onSubmit={handleQuestionSubmit}
              isLoading={isQueryLoading}
            />
            {queryError && (
              <ErrorMessage 
                error={queryError} 
                onDismiss={() => setQueryError(null)} 
              />
            )}
            <AnswerDisplay 
              answer={answer}
              isLoading={isQueryLoading}
              error={null}
            />
          </div>
          <div className="right-column">
            {objectListError && (
              <ErrorMessage 
                error={objectListError} 
                onDismiss={() => setObjectListError(null)} 
              />
            )}
            <ObjectListEditor 
              onUpdate={handleObjectListUpdate}
              onFetch={handleObjectListFetch}
              isLoading={isObjectListLoading}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
