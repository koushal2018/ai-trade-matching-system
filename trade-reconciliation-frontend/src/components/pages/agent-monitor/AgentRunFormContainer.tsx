import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AgentRunForm from './AgentRunForm';
import { AgentRunConfig } from '../../../types/agent';
import { AgentService } from '../../../services/agent/AgentService';
import { useToast } from '../../../context/ToastContext';

const AgentRunFormContainer: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (config: AgentRunConfig) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const agentService = AgentService.getInstance();
      const runId = await agentService.triggerRun(config);
      
      setSuccess(`Agent run started successfully with ID: ${runId}`);
      showToast('success', `Agent run started successfully with ID: ${runId}`);
      
      // Redirect to the active runs tab after a short delay
      setTimeout(() => {
        navigate('/agent-monitor', { state: { activeTab: 1, runId } });
      }, 1500);
    } catch (error) {
      const errorMessage = (error as Error).message;
      setError(errorMessage);
      showToast('error', `Failed to start agent run: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error starting agent run</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="rounded-md bg-green-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Success</h3>
              <div className="mt-2 text-sm text-green-700">
                <p>{success}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <AgentRunForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
      />
    </div>
  );
};

export default AgentRunFormContainer;