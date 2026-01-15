import React, { useState, useEffect } from 'react';
import './ObjectListEditor.css';
import ErrorMessage from './ErrorMessage';

interface ObjectListEditorProps {
  onUpdate: (objects: any[]) => Promise<void>;
  onFetch: () => Promise<{ objects: any[]; created_at?: string; updated_at?: string }>;
  isLoading: boolean;
}

const ObjectListEditor: React.FC<ObjectListEditorProps> = ({ onUpdate, onFetch, isLoading }) => {
  const [jsonText, setJsonText] = useState('');
  const [validationError, setValidationError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [createdAt, setCreatedAt] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [isLoadingData, setIsLoadingData] = useState(true);

  // Fetch saved drawing on mount
  useEffect(() => {
    const fetchSavedDrawing = async () => {
      try {
        const data = await onFetch();
        if (data.objects && data.objects.length > 0) {
          setJsonText(JSON.stringify(data.objects, null, 2));
          setCreatedAt(data.created_at || null);
          setUpdatedAt(data.updated_at || null);
        } else {
          setJsonText('[]');
        }
      } catch (err) {
        console.error('Failed to fetch saved drawing:', err);
        setJsonText('[]');
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchSavedDrawing();
  }, [onFetch]);

  const validateJSON = (text: string): { valid: boolean; objects?: any[]; error?: string } => {
    if (!text.trim()) {
      return { valid: false, error: 'JSON cannot be empty' };
    }

    try {
      const parsed = JSON.parse(text);
      
      if (!Array.isArray(parsed)) {
        return { valid: false, error: 'JSON must be an array of objects' };
      }

      return { valid: true, objects: parsed };
    } catch (err: any) {
      return { valid: false, error: `Invalid JSON: ${err.message}` };
    }
  };

  const handleUpdate = async () => {
    setValidationError('');
    setSuccessMessage('');

    const validation = validateJSON(jsonText);
    
    if (!validation.valid) {
      setValidationError(validation.error || 'Invalid JSON');
      return;
    }

    try {
      await onUpdate(validation.objects!);
      
      // Refresh the data to get new timestamps
      const data = await onFetch();
      setCreatedAt(data.created_at || null);
      setUpdatedAt(data.updated_at || null);
      
      setSuccessMessage('Drawing updated successfully');
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      // Error is handled by parent component
      // Just clear local validation error
      setValidationError('');
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJsonText(e.target.value);
    setValidationError('');
    setSuccessMessage('');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (isLoadingData) {
    return (
      <div className="object-list-editor-container">
        <p>Loading saved drawing...</p>
      </div>
    );
  }

  return (
    <div className="object-list-editor-container">
      <h3>Drawing JSON Editor</h3>
      <p className="editor-description">
        View and edit your drawing JSON. Changes are saved to your account.
      </p>
      
      {/* Timestamp Display */}
      {(createdAt || updatedAt) && (
        <div className="timestamp-info">
          {createdAt && (
            <div className="timestamp-item">
              <strong>Created:</strong> {formatDate(createdAt)}
            </div>
          )}
          {updatedAt && (
            <div className="timestamp-item">
              <strong>Last Updated:</strong> {formatDate(updatedAt)}
            </div>
          )}
        </div>
      )}
      
      <textarea
        value={jsonText}
        onChange={handleTextChange}
        placeholder='[{"id": "obj_001", "type": "example", "properties": {...}}]'
        disabled={isLoading}
        className="json-textarea"
        rows={15}
      />
      {validationError && (
        <ErrorMessage 
          error={validationError} 
          onDismiss={() => setValidationError('')} 
        />
      )}
      {successMessage && <div className="success-message">{successMessage}</div>}
      <button 
        onClick={handleUpdate} 
        disabled={isLoading}
        className="update-button"
      >
        {isLoading ? 'Saving...' : 'Save Drawing'}
      </button>
    </div>
  );
};

export default ObjectListEditor;
