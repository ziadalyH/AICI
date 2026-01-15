import React, { useState } from 'react';
import './QuestionInput.css';

interface QuestionInputProps {
  onSubmit: (question: string) => Promise<void>;
  isLoading: boolean;
}

const QuestionInput: React.FC<QuestionInputProps> = ({ onSubmit, isLoading }) => {
  const [question, setQuestion] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      await onSubmit(question.trim());
      setQuestion(''); // Clear input after successful submission
    } catch (err: any) {
      setError(err.message || 'Failed to submit question');
    }
  };

  return (
    <div className="question-input-container">
      <h3>Ask a Question</h3>
      <form onSubmit={handleSubmit} className="question-form">
        <div className="input-group">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your natural-language question..."
            disabled={isLoading}
            className="question-input"
          />
          <button type="submit" disabled={isLoading || !question.trim()}>
            {isLoading ? 'Processing...' : 'Submit'}
          </button>
        </div>
        {error && <div className="error-message">{error}</div>}
      </form>
    </div>
  );
};

export default QuestionInput;
