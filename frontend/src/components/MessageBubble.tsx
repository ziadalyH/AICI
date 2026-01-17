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
}

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="message-content">
        {message.content.split('\n').map((line, index) => (
          <p key={index}>{line || '\u00A0'}</p>
        ))}
      </div>

      {message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          <button 
            className="sources-toggle"
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? '▼' : '▶'} {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
          </button>

          {showSources && (
            <div className="sources-list">
              {message.sources.map((source, index) => (
                <div 
                  key={index} 
                  className={`source-item ${source.selected ? 'selected' : ''}`}
                >
                  <div className="source-header">
                    <span className="source-document">
                      {source.selected && <span className="selected-badge">✓ Used</span>}
                      {source.document}
                    </span>
                    <span className="source-location">
                      Page {source.page}
                      {source.paragraph !== undefined && `, Para ${source.paragraph}`}
                    </span>
                  </div>
                  {source.title && (
                    <div className="source-title">{source.title}</div>
                  )}
                  {source.snippet && (
                    <div className="source-snippet">
                      "{source.snippet.substring(0, 200)}..."
                    </div>
                  )}
                  {source.relevance !== undefined && (
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
