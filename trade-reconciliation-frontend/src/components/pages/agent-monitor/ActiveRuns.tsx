import React, { useState, useEffect } from 'react';
import { AgentRun } from '../../../types/agent';
import { AgentService } from '../../../services/agent/AgentService';
import { useToast } from '../../../context/ToastContext';
import RunStatusIndicator from './RunStatusIndicator';
import CancelRunModal from './CancelRunModal';

interface ActiveRunsProps {
  onViewDetails?: (runId: string) => void;
}

const ActiveRuns: React.FC<ActiveRunsProps> = ({ onViewDetails }) => {
  const { showToast } = useToast();
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [cancelRunId, setCancelRunId] = useState<string | null>(null);
  const [isCanceling, setIsCanceling] = useState(false);

  // Mock data for initial UI
  const mockRuns = [
    {
      id: 'run-001',
      agentType: 'Trade PDF Processing',
      status: 'running' as any,
      progress: 75,
      startTime: '2025-07-20T10:15:00Z',
      config: {
        agentType: 'trade-pdf-processing',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      }
    },
    {
      id: 'run-002',
      agentType: 'Trade Matching',
      status: 'queued' as any,
      progress: 0,
      config: {
        agentType: 'trade-matching',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      }
    },
    {
      id: 'run-003',
      agentType: 'Reconciliation',
      status: 'idle' as any,
      progress: 0,
      config: {
        agentType: 'reconciliation',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      }
    }
  ] as AgentRun[];

  // Fetch active runs
  useEffect(() => {
    const fetchActiveRuns = async () => {
      if (isRefreshing) {
        return;
      }
      
      setIsLoading(true);
      setError(null);

      try {
        // In a real implementation, we would call the API
        // const agentService = AgentService.getInstance();
        // const activeRuns = await agentService.getActiveRuns();
        
        // For now, use mock data
        setRuns(mockRuns);
        setIsConnected(true);
        setLastUpdated(new Date());
      } catch (error) {
        const errorMessage = (error as Error).message;
        setError(errorMessage);
        showToast('error', `Failed to fetch active runs: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchActiveRuns();
    
    // Set up auto-refresh
    let intervalId: NodeJS.Timeout | null = null;
    
    if (autoRefresh) {
      intervalId = setInterval(() => {
        setIsRefreshing(true);
        fetchActiveRuns().finally(() => {
          setIsRefreshing(false);
        });
      }, 5000); // Refresh every 5 seconds
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh, showToast]);

  // Subscribe to real-time updates
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const subscribeToUpdates = async () => {
      try {
        const agentService = AgentService.getInstance();
        unsubscribe = await agentService.subscribeToRunStatus((updatedRuns) => {
          // Check for status changes
          setRuns(prevRuns => {
            // Find runs that have changed status
            const statusChanges = updatedRuns.filter(newRun => {
              const oldRun = prevRuns.find(r => r.id === newRun.id);
              return oldRun && oldRun.status !== newRun.status;
            });
            
            // Show notifications for status changes
            statusChanges.forEach(run => {
              if (run.status === 'completed') {
                showToast('success', `Agent run ${run.id} completed successfully`);
              } else if (run.status === 'failed') {
                showToast('error', `Agent run ${run.id} failed: ${run.error || 'Unknown error'}`);
              } else if (run.status === 'cancelled') {
                showToast('info', `Agent run ${run.id} was cancelled`);
              }
            });
            
            return updatedRuns;
          });
          
          setLastUpdated(new Date());
        });
      } catch (error) {
        const errorMessage = (error as Error).message;
        setError(errorMessage);
        showToast('error', `Failed to subscribe to run status updates: ${errorMessage}`);
      }
    };

    // In a real implementation, we would subscribe to updates
    // subscribeToUpdates();
    
    // For demo purposes, simulate a run completion after 10 seconds
    const simulateRunCompletion = setTimeout(() => {
      if (runs.length > 0 && runs[0].status === 'running') {
        const updatedRuns = [...runs];
        updatedRuns[0] = { ...updatedRuns[0], status: 'completed' as any, progress: 100 };
        setRuns(updatedRuns);
        showToast('success', `Agent run ${updatedRuns[0].id} completed successfully`);
        setLastUpdated(new Date());
      }
    }, 10000);

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
      clearTimeout(simulateRunCompletion);
    };
  }, [showToast, runs]);

  // Open cancel confirmation modal
  const openCancelModal = (runId: string) => {
    setCancelRunId(runId);
  };
  
  // Close cancel confirmation modal
  const closeCancelModal = () => {
    setCancelRunId(null);
  };
  
  // Handle run cancellation
  const handleCancelRun = async () => {
    if (!cancelRunId) return;
    
    setIsCanceling(true);
    
    try {
      const agentService = AgentService.getInstance();
      await agentService.cancelRun(cancelRunId);
      
      showToast('success', 'Agent run cancelled successfully');
      
      // Update the run status in the UI
      setRuns(prevRuns => 
        prevRuns.map(run => 
          run.id === cancelRunId 
            ? { ...run, status: 'cancelled' as any } 
            : run
        )
      );
      
      // Close the modal
      closeCancelModal();
    } catch (error) {
      const errorMessage = (error as Error).message;
      showToast('error', `Failed to cancel run: ${errorMessage}`);
    } finally {
      setIsCanceling(false);
    }
  };

  // Handle view details
  const handleViewDetails = (runId: string) => {
    setSelectedRunId(runId);
    if (onViewDetails) {
      onViewDetails(runId);
    }
  };

  const getStatusBadgeClasses = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'idle':
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-green-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
      case 'queued':
        return (
          <svg className="h-4 w-4 text-yellow-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="h-4 w-4 text-blue-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="h-4 w-4 text-red-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'cancelled':
        return (
          <svg className="h-4 w-4 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return (
          <svg className="h-4 w-4 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium leading-6 text-gray-900">Active Agent Runs</h3>
          <p className="mt-1 text-sm text-gray-500">
            Monitor the status and progress of ongoing agent runs
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1 text-xs font-medium rounded-md ${
              autoRefresh ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
            }`}
          >
            {autoRefresh ? 'Auto-refresh On' : 'Auto-refresh Off'}
          </button>
          <button
            onClick={() => {
              setIsRefreshing(true);
              // In a real implementation, we would fetch the latest runs
              setTimeout(() => {
                setIsRefreshing(false);
                setLastUpdated(new Date());
              }, 500);
            }}
            className="px-3 py-1 text-xs font-medium rounded-md bg-gray-100 text-gray-800 hover:bg-gray-200"
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
              </span>
            ) : (
              'Refresh'
            )}
          </button>
        </div>
      </div>
      
      <RunStatusIndicator isConnected={isConnected} lastUpdated={lastUpdated} />
      
      {isLoading && !isRefreshing && (
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
      
      {!isLoading && !error && runs.length === 0 && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg p-6 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No active runs</h3>
          <p className="mt-1 text-sm text-gray-500">
            There are no active agent runs at the moment.
          </p>
        </div>
      )}
      
      {!isLoading && !error && runs.length > 0 && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <ul className="divide-y divide-gray-200">
            {runs.map((run) => (
              <li key={run.id} className={`p-4 hover:bg-gray-50 ${selectedRunId === run.id ? 'bg-blue-50' : ''}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <span className="font-medium text-gray-900">{run.agentType}</span>
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClasses(run.status)}`}>
                      {getStatusIcon(run.status)}
                      <span className="ml-1">{run.status.charAt(0).toUpperCase() + run.status.slice(1)}</span>
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {run.startTime ? new Date(run.startTime).toLocaleString() : 'Not started'}
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  {`Running ${run.agentType} agent...`}
                </div>
                
                {run.progress > 0 && (
                  <div className="mt-2 mb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-500">Progress</span>
                      <span className="font-medium">{run.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          run.status === 'failed' ? 'bg-red-600' : 
                          run.status === 'completed' ? 'bg-green-600' : 'bg-blue-600'
                        }`}
                        style={{width: `${run.progress}%`}}
                      ></div>
                    </div>
                  </div>
                )}
                
                <div className="mt-3 flex justify-between items-center">
                  <div className="text-xs text-gray-500">
                    ID: {run.id}
                  </div>
                  <div className="flex space-x-2">
                    <button 
                      className="px-3 py-1 text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      onClick={() => handleViewDetails(run.id)}
                    >
                      View Details
                    </button>
                    {run.status === 'running' && (
                      <button 
                        className="px-3 py-1 text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                        onClick={() => openCancelModal(run.id)}
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="mt-6">
        <h3 className="text-md font-semibold mb-3">Recent Agent Logs</h3>
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="bg-gray-50 p-4 max-h-64 overflow-y-auto">
            <div className="space-y-2 font-mono text-sm">
              <div className="text-green-600">[2025-07-20 10:18:15] PDF Processing: Successfully extracted 45 trades from document_001.pdf</div>
              <div className="text-blue-600">[2025-07-20 10:18:10] Matching: Found 42 potential matches for trade batch #123</div>
              <div className="text-yellow-600">[2025-07-20 10:18:05] Validation: 3 trades require manual review</div>
              <div className="text-gray-600">[2025-07-20 10:17:58] System: Agent pipeline initialized</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Cancel Run Modal */}
      {cancelRunId && (
        <CancelRunModal
          isOpen={!!cancelRunId}
          onClose={closeCancelModal}
          onConfirm={handleCancelRun}
          runId={cancelRunId}
          agentType={runs.find(run => run.id === cancelRunId)?.agentType || ''}
          isLoading={isCanceling}
        />
      )}
    </div>
  );
};

export default ActiveRuns;