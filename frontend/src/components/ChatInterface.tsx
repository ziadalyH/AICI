import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';
import MessageBubble from './MessageBubble';
import apiClient from '../services/apiClient';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
  knowledgeSummary?: {
    overview: string;
    topics: string[];
    suggested_questions: string[];
  };
}

interface ChatInterfaceProps {
  onSendMessage: (message: string) => Promise<{ 
    answer: string; 
    sources?: any[];
    knowledge_summary?: {
      overview: string;
      topics: string[];
      suggested_questions: string[];
    };
  }>;
}

interface KnowledgeSummary {
  overview: string;
  topics: string[];
  suggested_questions: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onSendMessage }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAgenticMode, setIsAgenticMode] = useState(false);
  const [knowledgeSummary, setKnowledgeSummary] = useState<KnowledgeSummary | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load knowledge summary on mount
  useEffect(() => {
    const loadSummary = async () => {
      try {
        const summary = await apiClient.getKnowledgeSummary();
        setKnowledgeSummary(summary);
      } catch (error) {
        console.error('Failed to load knowledge summary:', error);
      } finally {
        setIsLoadingSummary(false);
      }
    };

    loadSummary();
  }, []);

  // Listen for question population events from MessageBubble
  useEffect(() => {
    const handlePopulateQuestion = (event: CustomEvent) => {
      setInput(event.detail);
    };

    window.addEventListener('populateQuestion', handlePopulateQuestion as EventListener);
    
    return () => {
      window.removeEventListener('populateQuestion', handlePopulateQuestion as EventListener);
    };
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Use agentic mode if toggle is enabled
      const response = isAgenticMode 
        ? await apiClient.queryAgentic(userMessage.content)
        : await onSendMessage(userMessage.content);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        knowledgeSummary: response.knowledge_summary || undefined,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to get response'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStarterClick = (starter: string) => {
    setInput(starter);
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>Q&A Assistant</h3>
        <div className="mode-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={isAgenticMode}
              onChange={(e) => setIsAgenticMode(e.target.checked)}
              className="toggle-checkbox"
            />
            <span className="toggle-slider"></span>
            <span className="toggle-text">
              {isAgenticMode ? '🤖 Agentic Mode' : '⚡ Standard Mode'}
            </span>
          </label>
          <div className="mode-description">
            {isAgenticMode 
              ? 'Multi-step reasoning with tool use' 
              : 'Fast single-shot inference'}
          </div>
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="knowledge-summary">
            {isLoadingSummary ? (
              <div className="summary-loading">
                <div className="loading-spinner"></div>
                <p className="text-muted">Loading knowledge base...</p>
              </div>
            ) : knowledgeSummary ? (
              <>
                <div className="summary-header">
                  <h4>Knowledge Base</h4>
                  <p className="summary-overview">{knowledgeSummary.overview}</p>
                </div>

                {knowledgeSummary.topics && knowledgeSummary.topics.length > 0 && (
                  <div className="summary-section">
                    <h5>Topics Covered</h5>
                    <div className="topic-tags">
                      {knowledgeSummary.topics.map((topic, index) => (
                        <span key={index} className="topic-tag">{topic}</span>
                      ))}
                    </div>
                  </div>
                )}

                {knowledgeSummary.suggested_questions && knowledgeSummary.suggested_questions.length > 0 && (
                  <div className="summary-section">
                    <h5>Try asking:</h5>
                    <div className="suggested-questions">
                      {knowledgeSummary.suggested_questions.map((question, index) => (
                        <button
                          key={index}
                          className="question-button"
                          onClick={() => handleStarterClick(question)}
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="summary-fallback">
                <p>Start a conversation by asking a question below.</p>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="loading-message">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isLoading}
          className="chat-input"
        />
        <button 
          type="submit" 
          disabled={!input.trim() || isLoading}
          className="send-button"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
