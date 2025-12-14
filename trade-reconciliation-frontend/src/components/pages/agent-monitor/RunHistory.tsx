import React, { useState, useEffect } from 'react';
import { AgentRun, RunHistoryFilters as RunHistoryFiltersType } from '../../../types/agent';
import { AgentService } from '../../../services/agent/AgentService';
import { useToast } from '../../../context/ToastContext';
import RunHistoryFilters from './RunHistoryFilters';
import RunDetailView from './RunDetailView';
import RunComparisonView from './RunComparisonView';

interface RunHistoryProps {
  onViewDetails?: (runId: string) => void;
}

const RunHistory: React.FC<RunHistoryProps> = ({ onViewDetails }) => {
  const { showToast } = useToast();
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [filteredRuns, setFilteredRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
  const [isCompareMode, setIsCompareMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<RunHistoryFiltersType>({});
  const [activeTab, setActiveTab] = useState<'details' | 'thinking' | 'config' | 'results'>('details');
  
  // Mock data for initial UI
  const mockHistoryRuns = [
    {
      id: 'run-001',
      agentType: 'Trade PDF Processing',
      status: 'completed' as any,
      progress: 100,
      startTime: '2025-07-19T14:30:00Z',
      endTime: '2025-07-19T14:35:12Z',
      config: {
        agentType: 'trade-pdf-processing',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      },
      results: {
        summary: 'Processed 78 trades from 3 documents',
        outputData: {
          processedTrades: 78,
          documentCount: 3
        }
      },
      metrics: {
        duration: 312,
        resourceUsage: {
          cpu: 0.45,
          memory: 256
        }
      }
    },
    {
      id: 'run-002',
      agentType: 'Trade Matching',
      status: 'completed' as any,
      progress: 100,
      startTime: '2025-07-19T14:36:00Z',
      endTime: '2025-07-19T14:38:45Z',
      config: {
        agentType: 'trade-matching',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      },
      results: {
        summary: 'Matched 72 trades, 6 unmatched',
        outputData: {
          matchedTrades: 72,
          unmatchedTrades: 6
        }
      },
      metrics: {
        duration: 165,
        resourceUsage: {
          cpu: 0.35,
          memory: 192
        }
      }
    },
    {
      id: 'run-003',
      agentType: 'Reconciliation',
      status: 'failed' as any,
      progress: 30,
      startTime: '2025-07-19T14:40:00Z',
      endTime: '2025-07-19T14:40:30Z',
      error: 'Database connection timeout',
      config: {
        agentType: 'reconciliation',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      },
      metrics: {
        duration: 30,
        resourceUsage: {
          cpu: 0.25,
          memory: 128
        }
      }
    },
    {
      id: 'run-004',
      agentType: 'Trade PDF Processing',
      status: 'completed' as any,
      progress: 100,
      startTime: '2025-07-18T09:15:00Z',
      endTime: '2025-07-18T09:18:22Z',
      config: {
        agentType: 'trade-pdf-processing',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      },
      results: {
        summary: 'Processed 45 trades from 2 documents',
        outputData: {
          processedTrades: 45,
          documentCount: 2
        }
      },
      metrics: {
        duration: 202,
        resourceUsage: {
          cpu: 0.40,
          memory: 224
        }
      }
    },
    {
      id: 'run-005',
      agentType: 'Trade Matching',
      status: 'completed' as any,
      progress: 100,
      startTime: '2025-07-18T09:20:00Z',
      endTime: '2025-07-18T09:21:15Z',
      config: {
        agentType: 'trade-matching',
        parameters: {
          matchingThreshold: 0.85,
          numericTolerance: 0.001,
          reportBucket: 'reconciliation-reports'
        }
      },
      results: {
        summary: 'Matched 45 trades, 0 unmatched',
        outputData: {
          matchedTrades: 45,
          unmatchedTrades: 0
        }
      },
      metrics: {
        duration: 75,
        resourceUsage: {
          cpu: 0.30,
          memory: 160
        }
      }
    }
  ] as AgentRun[];

  // Fetch run history
  useEffect(() => {
    const fetchRunHistory = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // In a real implementation, we would call the API
        // const agentService = AgentService.getInstance();
        // const response = await agentService.getRunHistory({
        //   ...filters,
        //   page: currentPage,
        //   pageSize: 10
        // });
        
        // For now, use mock data
        // Apply filters to mock data
        let filtered = [...mockHistoryRuns];
        
        if (filters.agentType) {
          filtered = filtered.filter(run => 
            run.agentType.toLowerCase().includes(filters.agentType!.toLowerCase())
          );
        }
        
        if (filters.status) {
          filtered = filtered.filter(run => run.status === filters.status);
        }
        
        if (filters.startDate) {
          const startDate = new Date(filters.startDate);
          filtered = filtered.filter(run => 
            new Date(run.startTime || '') >= startDate
          );
        }
        
        if (filters.endDate) {
          const endDate = new Date(filters.endDate);
          filtered = filtered.filter(run => 
            new Date(run.startTime || '') <= endDate
          );
        }
        
        // Filter by archived status
        if (filters.showArchived !== undefined) {
          if (!filters.showArchived) {
            // Only show non-archived runs
            filtered = filtered.filter(run => !run.archived);
          }
          // If showArchived is true, include all runs (both archived and non-archived)
        }
        
        // Sort
        const sortBy = filters.sortBy || 'startTime';
        const sortDirection = filters.sortDirection || 'desc';
        
        filtered.sort((a, b) => {
          let aValue: any = a[sortBy as keyof AgentRun];
          let bValue: any = b[sortBy as keyof AgentRun];
          
          if (sortBy === 'startTime' || sortBy === 'endTime') {
            aValue = aValue ? new Date(aValue).getTime() : 0;
            bValue = bValue ? new Date(bValue).getTime() : 0;
          }
          
          if (sortDirection === 'asc') {
            return aValue > bValue ? 1 : -1;
          } else {
            return aValue < bValue ? 1 : -1;
          }
        });
        
        setRuns(mockHistoryRuns);
        setFilteredRuns(filtered);
        setTotalPages(Math.ceil(filtered.length / 10));
      } catch (error) {
        const errorMessage = (error as Error).message;
        setError(errorMessage);
        showToast('error', `Failed to fetch run history: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRunHistory();
  }, [filters, currentPage, showToast]);

  // Handle filter change
  const handleFilterChange = (newFilters: RunHistoryFiltersType) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  // Handle filter reset
  const handleFilterReset = () => {
    setFilters({});
    setCurrentPage(1);
  };

  // Handle run selection
  const handleRunSelect = (runId: string, isMultiSelect: boolean = false) => {
    if (isMultiSelect) {
      // In multi-select mode
      if (selectedRuns.includes(runId)) {
        // If already selected, remove it
        setSelectedRuns(selectedRuns.filter(id => id !== runId));
      } else {
        // Add to selection
        setSelectedRuns([...selectedRuns, runId]);
      }
    } else {
      // In single-select mode
      setSelectedRun(runId);
      setSelectedRuns([]);
      if (onViewDetails) {
        onViewDetails(runId);
      }
    }
  };
  
  // Toggle compare mode
  const toggleCompareMode = () => {
    setIsCompareMode(!isCompareMode);
    if (!isCompareMode) {
      // Entering compare mode
      setSelectedRun(null);
      setSelectedRuns([]);
    } else {
      // Exiting compare mode
      setSelectedRuns([]);
    }
  };
  
  // Start comparison
  const startComparison = () => {
    if (selectedRuns.length < 2) {
      showToast('error', 'Please select at least 2 runs to compare');
      return;
    }
    
    // The comparison view will be shown automatically when selectedRuns has 2+ items
    showToast('success', `Comparing ${selectedRuns.length} runs`);
  };

  // Handle pagination
  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  // Handle rerun
  const handleRerun = async (runId: string) => {
    try {
      const run = runs.find(r => r.id === runId);
      if (!run) return;
      
      const agentService = AgentService.getInstance();
      const newRunId = await agentService.triggerRun(run.config);
      
      showToast('success', `Agent run restarted with ID: ${newRunId}`);
    } catch (error) {
      const errorMessage = (error as Error).message;
      showToast('error', `Failed to restart run: ${errorMessage}`);
    }
  };

  // Import export utilities
  const { 
    convertRunToCSV, 
    downloadFile, 
    generateShareableLink, 
    copyToClipboard 
  } = require('../../../utils/exportUtils');
  
  // Handle export
  const handleExport = (runId: string) => {
    const run = runs.find(r => r.id === runId);
    if (!run) return;
    
    // Show export options in the RunDetailView component
    // The RunDetailView component will handle the actual export
  };

  const getStatusBadgeClasses = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Calculate duration from start and end time
  const calculateDuration = (startTime?: string, endTime?: string): string => {
    if (!startTime || !endTime) return 'N/A';
    
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();
    const durationMs = end - start;
    
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    
    return `${minutes}m ${seconds}s`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium leading-6 text-gray-900">Run History</h3>
        <p className="mt-1 text-sm text-gray-500">
          View historical agent runs and their results
        </p>
      </div>
      
      <RunHistoryFilters onFilterChange={handleFilterChange} onReset={handleFilterReset} />
      
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
      
      {!isLoading && !error && filteredRuns.length === 0 && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg p-6 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No runs found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No agent runs match your current filters.
          </p>
        </div>
      )}
      
      {!isLoading && !error && filteredRuns.length > 0 && (
        <div className="flex space-x-4">
          <div className="w-1/3 bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-700">Run History</h3>
                <div className="flex items-center space-x-2">
                  <div className="text-xs text-gray-500">
                    {filteredRuns.length} {filteredRuns.length === 1 ? 'run' : 'runs'} found
                  </div>
                  <button
                    onClick={toggleCompareMode}
                    className={`px-2 py-1 text-xs font-medium rounded-md ${
                      isCompareMode 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {isCompareMode ? 'Cancel Compare' : 'Compare Runs'}
                  </button>
                </div>
              </div>
              {isCompareMode && (
                <div className="mt-2 px-2 py-1 bg-blue-50 rounded text-xs text-blue-800 flex justify-between items-center">
                  <span>Select runs to compare ({selectedRuns.length} selected)</span>
                  <button
                    onClick={startComparison}
                    disabled={selectedRuns.length < 2}
                    className="px-2 py-0.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Compare
                  </button>
                </div>
              )}
            </div>
            <ul className="divide-y divide-gray-200">
              {filteredRuns.map((run) => (
                <li 
                  key={run.id}
                  className={`px-4 py-3 hover:bg-gray-50 cursor-pointer ${
                    isCompareMode
                      ? selectedRuns.includes(run.id) ? 'bg-blue-50' : ''
                      : selectedRun === run.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={(e) => handleRunSelect(run.id, isCompareMode || e.ctrlKey || e.metaKey)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {isCompareMode && (
                        <input
                          type="checkbox"
                          checked={selectedRuns.includes(run.id)}
                          onChange={() => handleRunSelect(run.id, true)}
                          onClick={(e) => e.stopPropagation()}
                          className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      )}
                      <p className="text-sm font-medium text-gray-900 truncate">{run.agentType}</p>
                    </div>
                    <span className={`px-2 py-1 ${getStatusBadgeClasses(run.status)} rounded-full text-xs`}>
                      {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
                    </span>
                  </div>
                  <div className="mt-1">
                    <p className="text-xs text-gray-500">
                      {new Date(run.startTime || '').toLocaleString()} • {calculateDuration(run.startTime, run.endTime)}
                    </p>
                  </div>
                  <p className="mt-1 text-xs text-gray-600 truncate">
                    {run.results?.summary || run.error || 'No results available'}
                  </p>
                </li>
              ))}
            </ul>
            <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
              <button 
                className="px-3 py-1 text-xs font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <span className="text-xs text-gray-500">Page {currentPage} of {totalPages}</span>
              <button 
                className="px-3 py-1 text-xs font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          </div>
          
          <div className="w-2/3 bg-white shadow sm:rounded-md">
            {selectedRuns.length >= 2 ? (
              <RunComparisonView 
                runs={filteredRuns.filter(run => selectedRuns.includes(run.id))}
                onClose={() => setSelectedRuns([])}
              />
            ) : selectedRun ? (
              <>
                {filteredRuns.find(run => run.id === selectedRun) ? (
                  <RunDetailView 
                    run={filteredRuns.find(run => run.id === selectedRun)!}
                    onRerun={handleRerun}
                    onExport={handleExport}
                  />
                ) : (
                  <div className="p-4 text-center text-gray-500">
                    Run not found
                  </div>
                )}
              </>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No run selected</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {isCompareMode 
                    ? 'Select at least 2 runs to compare' 
                    : 'Select a run from the list to view details'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RunHistory;