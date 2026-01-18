import React, { useState } from 'react';
import './MessageBubble.css';

interface Source {
  type: string;
  document: string;
  page: number;
  paragraph?: number;
  snippet?: string;
  relevance?: number;
  title?: string;
  selected?: boolean;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
  knowledgeSummary?: {
    overview: string;
    topics: string[];
    suggested_questions: string[];
  };
}

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Check if this is a drawing-only response
  const isDrawingResponse = message.sources && message.sources.length > 0 && 
    message.sources.every(s => s.type === 'drawing' || s.document === '[Drawing Analysis]' || s.document === 'Drawing Analysis');

  // Handler for clicking suggested questions
  const handleQuestionClick = (question: string) => {
    // Dispatch custom event to populate input
    const event = new CustomEvent('populateQuestion', { detail: question });
    window.dispatchEvent(event);
  };

  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="message-content">
        {message.content.split('\n').map((line, index) => (
          <p key={index}>{line || '\u00A0'}</p>
        ))}
      </div>

      {/* Show knowledge summary if available (when LLM refuses) */}
      {message.knowledgeSummary && (
        <div className="knowledge-summary">
          <button 
            className="summary-toggle"
            onClick={() => setShowSummary(!showSummary)}
          >
            {showSummary ? '▼' : '▶'} What can I help with?
          </button>

          {showSummary && (
            <div className="summary-content">
              <div className="summary-overview">
                <strong>Overview:</strong>
                <p>{message.knowledgeSummary.overview}</p>
              </div>

              <div className="summary-topics">
                <strong>Topics I can help with:</strong>
                <ul>
                  {message.knowledgeSummary.topics.map((topic, index) => (
                    <li key={index}>{topic}</li>
                  ))}
                </ul>
              </div>

              <div className="summary-questions">
                <strong>Try asking:</strong>
                <ul>
                  {message.knowledgeSummary.suggested_questions.map((question, index) => (
                    <li 
                      key={index}
                      onClick={() => handleQuestionClick(question)}
                      style={{ cursor: 'pointer' }}
                    >
                      {question}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {message.sources && message.sources.length > 0 && (
        <div className={`message-sources ${isDrawingResponse ? 'drawing-sources' : 'pdf-sources'}`}>
          <button 
            className="sources-toggle"
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? '▼' : '▶'} {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            {isDrawingResponse && ' 🎨'}
          </button>

          {showSources && (
            <div className="sources-list">
              {message.sources.map((source, index) => (
                <div 
                  key={index} 
                  className={`source-item ${source.selected ? 'selected' : ''} ${source.type === 'drawing' ? 'drawing-source' : 'pdf-source'}`}
                >
                  <div className="source-header">
                    <span className="source-document">
                      {source.selected && <span className="selected-badge">✓ Used</span>}
                      {source.type === 'drawing' && <span className="drawing-badge">🎨 Drawing</span>}
                      {source.document}
                    </span>
                    {source.type !== 'drawing' && source.document !== '[Drawing Analysis]' && source.document !== 'Drawing Analysis' && (
                      <span className="source-location">
                        Page {source.page}
                        {source.paragraph !== undefined && `, Para ${source.paragraph}`}
                      </span>
                    )}
                  </div>
                  {source.title && (
                    <div className="source-title">{source.title}</div>
                  )}
                  {source.snippet && (
                    <div className="source-snippet">
                      "{source.snippet.substring(0, 200)}..."
                    </div>
                  )}
                  {source.relevance !== undefined && source.type !== 'drawing' && (
                    <div className="source-relevance">
                      Relevance: {(source.relevance * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="message-timestamp">{formatTime(message.timestamp)}</div>
    </div>
  );
};

export default MessageBubble;
