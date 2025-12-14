import React, { useState } from 'react';
import { AgentThinkingStep } from '../../../types/agent';

interface ErrorSummaryProps {
  steps: AgentThinkingStep[];
  onErrorClick: (errorId: string) => void;
}

const ErrorSummary: React.FC<ErrorSummaryProps> = ({ steps, onErrorClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Filter out error steps
  const errorSteps = steps.filter(step => step.type === 'error');
  
  if (errorSteps.length === 0) {
    return null;
  }
  
  return (
    <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">
            {errorSteps.length} {errorSteps.length === 1 ? 'error' : 'errors'} detected in thinking process
          </h3>
          <div className="mt-2 text-sm text-red-700">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center font-medium hover:underline focus:outline-none"
            >
              {isExpanded ? 'Hide details' : 'Show details'}
              <svg
                className={`ml-1 h-4 w-4 transform ${isExpanded ? 'rotate-180' : ''}`}
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className="mt-4 space-y-2">
          {errorSteps.map((step) => (
            <div
              key={step.id}
              className="p-2 bg-white rounded border border-red-200 cursor-pointer hover:bg-red-50"
              onClick={() => onErrorClick(step.id)}
            >
              <div className="flex items-center justify-between">
                <div className="text-sm text-red-800 font-medium truncate">
                  {step.content.substring(0, 100)}
                  {step.content.length > 100 ? '...' : ''}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(step.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ErrorSummary;