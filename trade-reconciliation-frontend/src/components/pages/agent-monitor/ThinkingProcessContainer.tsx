import React, { useState, useEffect, useRef } from 'react';
import ThinkingProcess from './ThinkingProcess';
import ThinkingProcessFilters from './ThinkingProcessFilters';
import ErrorSummary from './ErrorSummary';
import { AgentThinkingStep, AgentThinkingStepType } from '../../../types/agent';
import { AgentService } from '../../../services/agent/AgentService';
import { ThinkingProcessService } from '../../../services/agent/ThinkingProcessService';
import { useToast } from '../../../context/ToastContext';

interface ThinkingProcessContainerProps {
  runId: string;
  autoScroll?: boolean;
}

const ThinkingProcessContainer: React.FC<ThinkingProcessContainerProps> = ({
  runId,
  autoScroll = true,
}) => {
  const { showToast } = useToast();
  const [steps, setSteps] = useState<AgentThinkingStep[]>([]);
  const [filteredSteps, setFilteredSteps] = useState<AgentThinkingStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<AgentThinkingStepType[]>([]);
  const [newStepIds, setNewStepIds] = useState<Set<string>>(new Set());
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const newStepTimeout = useRef<NodeJS.Timeout | null>(null);

  // Fetch initial thinking process data
  useEffect(() => {
    const fetchThinkingProcess = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const agentService = AgentService.getInstance();
        const thinkingSteps = await agentService.getThinkingProcess(runId);
        
        // Organize steps into a hierarchy
        const organizedSteps = ThinkingProcessService.organizeHierarchy(thinkingSteps);
        setSteps(organizedSteps);
        setFilteredSteps(organizedSteps);
      } catch (error) {
        const errorMessage = (error as Error).message;
        setError(errorMessage);
        showToast('error', `Failed to fetch thinking process: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchThinkingProcess();
  }, [runId, showToast]);

  // Subscribe to real-time updates
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const subscribeToUpdates = async () => {
      try {
        const agentService = AgentService.getInstance();
        unsubscribe = await agentService.subscribeToThinkingProcess(runId, (newStep) => {
          setSteps((prevSteps) => {
            // Check if the step already exists
            const stepExists = prevSteps.some((step) => step.id === newStep.id);
            if (stepExists) {
              return prevSteps;
            }

            // Mark the step as new for highlighting
            setNewStepIds(prev => {
              const updated = new Set(prev);
              updated.add(newStep.id);
              return updated;
            });
            
            // Clear the highlight after a delay
            if (newStepTimeout.current) {
              clearTimeout(newStepTimeout.current);
            }
            
            newStepTimeout.current = setTimeout(() => {
              setNewStepIds(prev => {
                const updated = new Set(prev);
                updated.delete(newStep.id);
                return updated;
              });
            }, 3000);

            // Add the new step to the hierarchy
            const updatedSteps = [...prevSteps];
            
            if (newStep.parentId) {
              // Find the parent step and add this as a child
              const findAndAddChild = (steps: AgentThinkingStep[]): boolean => {
                for (const step of steps) {
                  if (step.id === newStep.parentId) {
                    if (!step.children) {
                      step.children = [];
                    }
                    step.children.push(newStep);
                    return true;
                  }
                  
                  if (step.children && findAndAddChild(step.children)) {
                    return true;
                  }
                }
                return false;
              };
              
              if (!findAndAddChild(updatedSteps)) {
                // If parent not found, add as a root step
                updatedSteps.push(newStep);
              }
            } else {
              // Add as a root step
              updatedSteps.push(newStep);
            }
            
            return updatedSteps;
          });
        });
      } catch (error) {
        const errorMessage = (error as Error).message;
        setError(errorMessage);
        showToast('error', `Failed to subscribe to thinking process updates: ${errorMessage}`);
      }
    };

    subscribeToUpdates();

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
      
      if (newStepTimeout.current) {
        clearTimeout(newStepTimeout.current);
      }
    };
  }, [runId, showToast]);

  // Time range filter
  const [startTimeFilter, setStartTimeFilter] = useState<string>('');
  const [endTimeFilter, setEndTimeFilter] = useState<string>('');

  // Apply search and filters
  useEffect(() => {
    let result = steps;
    
    // Apply type filters
    if (selectedTypes.length > 0) {
      result = ThinkingProcessService.filterByType(result, selectedTypes);
    }
    
    // Apply search
    if (searchQuery) {
      result = ThinkingProcessService.search(result, searchQuery);
    }
    
    // Apply time range filter
    if (startTimeFilter && endTimeFilter) {
      const startTime = new Date(startTimeFilter).getTime();
      const endTime = new Date(endTimeFilter).getTime();
      
      result = result.filter(step => {
        const stepTime = new Date(step.timestamp).getTime();
        return stepTime >= startTime && stepTime <= endTime;
      });
    }
    
    setFilteredSteps(result);
  }, [steps, searchQuery, selectedTypes, startTimeFilter, endTimeFilter]);

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  // Handle filter change
  const handleFilterChange = (types: AgentThinkingStepType[]) => {
    setSelectedTypes(types);
  };
  
  // Handle time range change
  const handleTimeRangeChange = (startTime: string, endTime: string) => {
    setStartTimeFilter(startTime);
    setEndTimeFilter(endTime);
  };
  
  // Handle error click in the error summary
  const handleErrorClick = (errorId: string) => {
    // Find the error step
    const findErrorStep = (steps: AgentThinkingStep[]): AgentThinkingStep | null => {
      for (const step of steps) {
        if (step.id === errorId) {
          return step;
        }
        
        if (step.children) {
          const found = findErrorStep(step.children);
          if (found) {
            return found;
          }
        }
      }
      
      return null;
    };
    
    const errorStep = findErrorStep(steps);
    
    if (errorStep) {
      // Expand all parent steps
      const expandParents = (step: AgentThinkingStep, allSteps: AgentThinkingStep[]) => {
        if (!step.parentId) {
          return;
        }
        
        const findParentAndExpand = (steps: AgentThinkingStep[]): boolean => {
          for (const s of steps) {
            if (s.id === step.parentId) {
              setExpandedSteps(prev => {
                const updated = new Set(prev);
                updated.add(s.id);
                return updated;
              });
              return true;
            }
            
            if (s.children && findParentAndExpand(s.children)) {
              return true;
            }
          }
          
          return false;
        };
        
        findParentAndExpand(allSteps);
        
        // Find the parent step and continue expanding
        const findParent = (steps: AgentThinkingStep[]): AgentThinkingStep | null => {
          for (const s of steps) {
            if (s.id === step.parentId) {
              return s;
            }
            
            if (s.children) {
              const found = findParent(s.children);
              if (found) {
                return found;
              }
            }
          }
          
          return null;
        };
        
        const parent = findParent(allSteps);
        if (parent) {
          expandParents(parent, allSteps);
        }
      };
      
      expandParents(errorStep, steps);
      
      // Highlight the error step
      setNewStepIds(prev => {
        const updated = new Set(prev);
        updated.add(errorId);
        return updated;
      });
      
      // Clear the highlight after a delay
      setTimeout(() => {
        setNewStepIds(prev => {
          const updated = new Set(prev);
          updated.delete(errorId);
          return updated;
        });
      }, 3000);
    }
  };

  // Track connection status
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Update connection status and last updated time when new steps are received
  useEffect(() => {
    if (steps.length > 0) {
      setIsConnected(true);
      setLastUpdated(new Date());
    }
  }, [steps]);

  return (
    <div>
      {isLoading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {error && !isLoading && (
        <div className="rounded-md bg-red-50 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {!isLoading && !error && (
        <>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className={`h-3 w-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected - Receiving real-time updates' : 'Connecting...'}
              </span>
            </div>
            {lastUpdated && (
              <div className="text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>
          
          <ErrorSummary steps={steps} onErrorClick={handleErrorClick} />
          
          <ThinkingProcessFilters
            onSearch={handleSearch}
            onFilterChange={handleFilterChange}
            onTimeRangeChange={handleTimeRangeChange}
            selectedTypes={selectedTypes}
            searchQuery={searchQuery}
          />
          
          <div className="mt-4">
            <ThinkingProcess
              steps={filteredSteps}
              autoScroll={autoScroll}
              newStepIds={newStepIds}
              expandedSteps={expandedSteps}
              setExpandedSteps={setExpandedSteps}
            />
          </div>
        </>
      )}
    </div>
  );
};

export default ThinkingProcessContainer;