import React, { useState, useEffect, useRef } from 'react';
import { AgentThinkingStep, AgentThinkingStepType } from '../../../types/agent';
import { ThinkingProcessService } from '../../../services/agent/ThinkingProcessService';

interface ThinkingProcessProps {
  steps: AgentThinkingStep[];
  autoScroll?: boolean;
  newStepIds?: Set<string>;
  expandedSteps?: Set<string>;
  setExpandedSteps?: React.Dispatch<React.SetStateAction<Set<string>>>;
}

const ThinkingProcess: React.FC<ThinkingProcessProps> = ({
  steps,
  autoScroll = true,
  newStepIds = new Set(),
  expandedSteps = new Set<string>(),
  setExpandedSteps,
}) => {
  const [localExpandedSteps, setLocalExpandedSteps] = useState<Set<string>>(new Set());
  
  // Use either the provided expandedSteps or the local state
  const effectiveExpandedSteps = setExpandedSteps ? expandedSteps : localExpandedSteps;
  const effectiveSetExpandedSteps = setExpandedSteps || setLocalExpandedSteps;
  const endOfListRef = useRef<HTMLDivElement>(null);
  
  // Expand all error steps by default
  useEffect(() => {
    const errorStepIds = new Set<string>();
    
    const findErrorSteps = (steps: AgentThinkingStep[]) => {
      for (const step of steps) {
        if (step.type === 'error') {
          errorStepIds.add(step.id);
          
          // Also expand parent steps
          let currentStep = step;
          while (currentStep.parentId) {
            errorStepIds.add(currentStep.parentId);
            
            // Find the parent step
            const findParent = (parentId: string, steps: AgentThinkingStep[]): AgentThinkingStep | null => {
              for (const s of steps) {
                if (s.id === parentId) {
                  return s;
                }
                
                if (s.children) {
                  const found = findParent(parentId, s.children);
                  if (found) {
                    return found;
                  }
                }
              }
              
              return null;
            };
            
            const parent = findParent(currentStep.parentId, steps);
            if (!parent) {
              break;
            }
            
            currentStep = parent;
          }
        }
        
        if (step.children) {
          findErrorSteps(step.children);
        }
      }
    };
    
    findErrorSteps(steps);
    
    if (errorStepIds.size > 0) {
      effectiveSetExpandedSteps(prev => {
        const updated = new Set(prev);
        errorStepIds.forEach(id => updated.add(id));
        return updated;
      });
    }
  }, [steps, effectiveSetExpandedSteps]);

  // Auto-scroll to the bottom when new steps are added
  useEffect(() => {
    if (autoScroll && endOfListRef.current) {
      endOfListRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [steps, autoScroll]);

  // Toggle step expansion
  const toggleStepExpansion = (stepId: string) => {
    const newExpandedSteps = new Set(effectiveExpandedSteps);
    if (newExpandedSteps.has(stepId)) {
      newExpandedSteps.delete(stepId);
    } else {
      newExpandedSteps.add(stepId);
    }
    effectiveSetExpandedSteps(newExpandedSteps);
  };



  // Render a single thinking step
  const renderStep = (step: AgentThinkingStep, depth = 0) => {
    const hasChildren = step.children && step.children.length > 0;
    const isExpanded = effectiveExpandedSteps.has(step.id);
    const isError = step.type === 'error';
    
    return (
      <div key={step.id} className="mb-2">
        <div 
          className={`p-3 rounded-md ${ThinkingProcessService.getStepTypeClass(step.type)} hover:bg-opacity-80 transition-colors ${
            newStepIds.has(step.id) ? 'animate-pulse border-2 border-blue-500' : ''
          } ${isError ? 'border-2 border-red-500' : ''}`}
          style={{ marginLeft: `${depth * 20}px` }}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 mr-2">
              {hasChildren && (
                <button
                  onClick={() => toggleStepExpansion(step.id)}
                  className="p-1 rounded-full hover:bg-gray-200"
                >
                  <svg
                    className="h-4 w-4 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    {isExpanded ? (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    ) : (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    )}
                  </svg>
                </button>
              )}
              {isError && (
                <svg
                  className="h-5 w-5 text-red-500"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <div className="flex items-center mb-1">
                <span className={`text-xs font-medium uppercase mr-2 ${isError ? 'text-red-700' : ''}`}>
                  {step.type}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(step.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className={`whitespace-pre-wrap text-sm ${isError ? 'font-medium' : ''}`}>
                {ThinkingProcessService.formatStepContent(step)}
              </div>
              {step.metadata && Object.keys(step.metadata).length > 0 && (
                <div className="mt-2">
                  <details className="text-xs" open={isError}>
                    <summary className={`cursor-pointer ${isError ? 'text-red-600 font-medium' : 'text-gray-600'} hover:text-gray-800`}>
                      {isError ? 'Error Details' : 'Metadata'}
                    </summary>
                    <pre className={`mt-1 p-2 ${isError ? 'bg-red-50' : 'bg-gray-100'} rounded overflow-auto max-h-40`}>
                      {JSON.stringify(step.metadata, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
              {isError && (
                <div className="mt-2">
                  <button
                    className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    onClick={() => {
                      // Copy error details to clipboard
                      const errorText = `Error: ${step.content}\n\nTimestamp: ${step.timestamp}\n\nDetails: ${JSON.stringify(step.metadata, null, 2)}`;
                      navigator.clipboard.writeText(errorText);
                      alert('Error details copied to clipboard');
                    }}
                  >
                    Copy Error Details
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {step.children!.map(childStep => renderStep(childStep, depth + 1))}
          </div>
        )}
      </div>
    );
  };



  return (
    <div className="space-y-4">
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Thinking Process</h3>
          <div className="mt-4 border border-gray-200 rounded-md p-4 max-h-96 overflow-y-auto">
            {steps.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No thinking steps available yet.
              </div>
            ) : (
              <div className="space-y-2">
                {steps.map(step => renderStep(step))}
                <div ref={endOfListRef} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThinkingProcess;