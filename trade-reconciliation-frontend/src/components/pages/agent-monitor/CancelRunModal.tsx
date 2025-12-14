import React from 'react';
import Modal from '../../common/Modal';

interface CancelRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  runId: string;
  agentType: string;
  isLoading?: boolean;
}

const CancelRunModal: React.FC<CancelRunModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  runId,
  agentType,
  isLoading = false,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Cancel Agent Run" size="md">
      <div className="mt-2">
        <p className="text-sm text-gray-500">
          Are you sure you want to cancel this agent run? This action cannot be undone.
        </p>
        
        <div className="mt-4 bg-gray-50 p-4 rounded-md">
          <div className="text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Agent Type:</span>
              <span className="font-medium text-gray-900">{agentType}</span>
            </div>
            <div className="flex justify-between mt-2">
              <span className="text-gray-500">Run ID:</span>
              <span className="font-medium text-gray-900">{runId}</span>
            </div>
          </div>
        </div>
        
        <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                Canceling a run may result in incomplete data or inconsistent state. Any partial results may not be usable.
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
        <button
          type="button"
          className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:col-start-2 sm:text-sm"
          onClick={onConfirm}
          disabled={isLoading}
        >
          {isLoading ? 'Canceling...' : 'Cancel Run'}
        </button>
        <button
          type="button"
          className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
          onClick={onClose}
          disabled={isLoading}
        >
          Go Back
        </button>
      </div>
    </Modal>
  );
};

export default CancelRunModal;