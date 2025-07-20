import React, { useState, useEffect } from 'react';
import Modal from '../../common/Modal';
import { SavedConfiguration } from '../../../types/agent';
import { AgentService } from '../../../services/agent/AgentService';

interface LoadConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoad: (config: SavedConfiguration) => void;
}

const LoadConfigModal: React.FC<LoadConfigModalProps> = ({ isOpen, onClose, onLoad }) => {
  const [configurations, setConfigurations] = useState<SavedConfiguration[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);

  // Load configurations when modal opens
  useEffect(() => {
    if (isOpen) {
      loadConfigurations();
    }
  }, [isOpen]);

  // Load configurations from API
  const loadConfigurations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const agentService = AgentService.getInstance();
      const configs = await agentService.getSavedConfigurations();
      setConfigurations(configs);
      
      // Select the first configuration by default
      if (configs.length > 0 && !selectedConfigId) {
        setSelectedConfigId(configs[0].id);
      }
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle configuration selection
  const handleSelect = (configId: string) => {
    setSelectedConfigId(configId);
  };

  // Handle load button click
  const handleLoad = () => {
    if (!selectedConfigId) return;
    
    const selectedConfig = configurations.find(config => config.id === selectedConfigId);
    if (selectedConfig) {
      onLoad(selectedConfig);
      onClose();
    }
  };

  // Handle delete button click
  const handleDelete = async (configId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this configuration?')) {
      return;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      const agentService = AgentService.getInstance();
      await agentService.deleteConfiguration(configId);
      
      // Reload configurations
      await loadConfigurations();
      
      // If the deleted configuration was selected, clear selection
      if (selectedConfigId === configId) {
        setSelectedConfigId(null);
      }
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Load Configuration" size="lg">
      <div className="mt-4">
        {isLoading && (
          <div className="flex justify-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-red-50 p-4 mb-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {!isLoading && configurations.length === 0 && (
          <div className="text-center py-6">
            <p className="text-gray-500">No saved configurations found.</p>
          </div>
        )}

        {!isLoading && configurations.length > 0 && (
          <div className="max-h-96 overflow-y-auto">
            <ul className="divide-y divide-gray-200">
              {configurations.map((config) => (
                <li
                  key={config.id}
                  className={`px-4 py-4 cursor-pointer hover:bg-gray-50 ${
                    selectedConfigId === config.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleSelect(config.id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{config.name}</h4>
                      <p className="text-sm text-gray-500">
                        {new Date(config.updatedAt).toLocaleString()}
                      </p>
                      {config.description && (
                        <p className="mt-1 text-sm text-gray-600">{config.description}</p>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        onClick={(e) => handleDelete(config.id, e)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="mt-2">
                    <p className="text-xs text-gray-500">
                      Agent Type: <span className="font-medium">{config.config.agentType}</span>
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
          <button
            type="button"
            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm"
            onClick={handleLoad}
            disabled={isLoading || !selectedConfigId}
          >
            Load
          </button>
          <button
            type="button"
            className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default LoadConfigModal;