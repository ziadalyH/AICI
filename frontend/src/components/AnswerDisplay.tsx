import React from 'react';
import './AnswerDisplay.css';

interface AnswerDisplayProps {
  answer: string | null;
  isLoading: boolean;
  error: null; // Kept for backwards compatibility but not used
}

const AnswerDisplay: React.FC<AnswerDisplayProps> = ({ answer, isLoading }) => {
  if (isLoading) {
    return (
      <div className="answer-display-container">
        <h3>Answer</h3>
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Processing your question...</p>
        </div>
      </div>
    );
  }

  if (!answer) {
    return (
      <div className="answer-display-container">
        <h3>Answer</h3>
        <div className="placeholder-message">
          Submit a question to see the answer here.
        </div>
      </div>
    );
  }

  return (
    <div className="answer-display-container">
      <h3>Answer</h3>
      <div className="answer-content">
        {answer.split('\n').map((line, index) => (
          <p key={index}>{line || '\u00A0'}</p>
        ))}
      </div>
    </div>
  );
};

export default AnswerDisplay;
