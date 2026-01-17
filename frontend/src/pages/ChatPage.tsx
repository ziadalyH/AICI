import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatInterface from '../components/ChatInterface';
import ObjectListEditor from '../components/ObjectListEditor';
import apiClient from '../services/apiClient';
import './ChatPage.css';

function ChatPage() {
  const navigate = useNavigate();
  const [isObjectListLoading, setIsObjectListLoading] = useState(false);
  const [objectListError, setObjectListError] = useState<string | null>(null);

  const handleLogout = () => {
    apiClient.logout();
    navigate('/login');
  };

  const handleSendMessage = async (message: string) => {
    const response = await apiClient.query(message);
    return {
      answer: response.answer,
      sources: response.sources
    };
  };

  const handleClearHistory = async () => {
    await apiClient.clearConversationHistory();
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

  return (
    <div className="chat-page">
      <button onClick={handleLogout} className="logout-btn" title="Sign Out">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>

      <main className="chat-main">
        <div className="container">
          <div className="chat-grid">
            <div className="chat-column">
              <ChatInterface 
                onSendMessage={handleSendMessage}
                onClearHistory={handleClearHistory}
              />
            </div>
            <div className="sidebar-column">
              {objectListError && (
                <div className="alert alert-error">
                  {objectListError}
                  <button 
                    onClick={() => setObjectListError(null)}
                    className="alert-close"
                  >
                    ×
                  </button>
                </div>
              )}
              <ObjectListEditor 
                onUpdate={handleObjectListUpdate}
                onFetch={handleObjectListFetch}
                isLoading={isObjectListLoading}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
