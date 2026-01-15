import React from 'react';
import './ErrorMessage.css';

interface ErrorMessageProps {
  error: string | null;
  onDismiss?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ error, onDismiss }) => {
  if (!error) {
    return null;
  }

  // Map technical errors to user-friendly messages
  const getUserFriendlyMessage = (errorMsg: string): string => {
    const lowerError = errorMsg.toLowerCase();
    
    // Authentication errors
    if (lowerError.includes('invalid username or password')) {
      return 'Invalid username or password. Please try again.';
    }
    if (lowerError.includes('token expired') || lowerError.includes('authentication required')) {
      return 'Your session has expired. Please log in again.';
    }
    if (lowerError.includes('invalid authentication token')) {
      return 'Authentication failed. Please log in again.';
    }
    
    // Session errors
    if (lowerError.includes('session not found') || lowerError.includes('session expired')) {
      return 'Your session has expired. Please refresh the page and try again.';
    }
    
    // Query errors
    if (lowerError.includes('query cannot be empty')) {
      return 'Please enter a question before submitting.';
    }
    if (lowerError.includes('query exceeds maximum length')) {
      return 'Your question is too long. Please shorten it and try again.';
    }
    if (lowerError.includes('query processing timed out')) {
      return 'The request took too long to process. Please try again.';
    }
    
    // JSON errors
    if (lowerError.includes('invalid json')) {
      return 'Invalid JSON format. Please check your object list syntax.';
    }
    if (lowerError.includes('json')) {
      return 'There was an error with your object list format. Please check the JSON syntax.';
    }
    
    // Service availability errors
    if (lowerError.includes('ai service temporarily unavailable') || 
        lowerError.includes('ai agent unavailable')) {
      return 'The AI service is temporarily unavailable. Please try again in a moment.';
    }
    if (lowerError.includes('document retrieval service temporarily unavailable') ||
        lowerError.includes('vector database')) {
      return 'The document search service is temporarily unavailable. Please try again in a moment.';
    }
    if (lowerError.includes('service unavailable') || lowerError.includes('503')) {
      return 'The service is temporarily unavailable. Please try again in a moment.';
    }
    
    // Network errors
    if (lowerError.includes('network error') || lowerError.includes('failed to fetch')) {
      return 'Network error. Please check your connection and try again.';
    }
    
    // Generic errors
    if (lowerError.includes('an unexpected error occurred') || 
        lowerError.includes('internal server error')) {
      return 'An unexpected error occurred. Please try again.';
    }
    
    // Return original message if no mapping found
    return errorMsg;
  };

  const friendlyMessage = getUserFriendlyMessage(error);

  return (
    <div className="error-message-container">
      <div className="error-message-content">
        <div className="error-icon">⚠️</div>
        <div className="error-text">
          <strong>Error:</strong> {friendlyMessage}
        </div>
        {onDismiss && (
          <button 
            className="error-dismiss-button" 
            onClick={onDismiss}
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;
