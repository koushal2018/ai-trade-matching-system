import React, { useState, useEffect } from 'react';
import { AgentRun, AgentRunStatus } from '../../../types/agent';
import { useToast } from '../../../context/ToastContext';
import ThinkingProcessContainer from './ThinkingProcessContainer';
import { AgentService } from '../../../services/agent/AgentService';

interface RunDetailViewProps {
  run: AgentRun;
  onRerun?: (runId: string) => void;
  onExport?: (runId: string) => void;
}

const RunDetailView: React.FC<RunDetailViewProps> = ({ run, onRerun, onExport }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'details' | 'thinking' | 'config' | 'results'>('details');
  const [isLoading, setIsLoading] = useState(false);
  const [refreshedRun, setRefreshedRun] = useState<AgentRun | null>(null);
  const [confirmationModal, setConfirmationModal] = useState<{
    isOpen: boolean;
    itemId: string;
    newStatus: 'completed' | 'ignored' | 'pending';
    title: string;
    message: string;
  }>({
    isOpen: false,
    itemId: '',
    newStatus: 'completed',
    title: '',
    message: ''
  });

  // Fetch the latest run data when the component mounts or run ID changes
  useEffect(() => {
    const fetchRunDetails = async () => {
      if ((['running', 'queued'] as AgentRunStatus[]).includes(run.status)) {
        setIsLoading(true);
        try {
          const agentService = AgentService.getInstance();
          const latestRun = await agentService.getRun(run.id);
          setRefreshedRun(latestRun);
        } catch (error) {
          console.error('Failed to fetch latest run details:', error);
          // Fall back to the provided run data
        } finally {
          setIsLoading(false);
        }
      }
    };

    fetchRunDetails();
  }, [run.id, run.status]);

  // Use the refreshed run data if available, otherwise use the provided run
  const currentRun = refreshedRun || run;

  // Calculate duration from start and end time
  const calculateDuration = (startTime?: string, endTime?: string): string => {
    if (!startTime) return 'N/A';
    
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();
    const durationMs = end - start;
    
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    
    return `${minutes}m ${seconds}s`;
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

  // Handle rerun
  const handleRerun = () => {
    if (onRerun) {
      onRerun(currentRun.id);
    } else {
      showToast('info', 'Rerun functionality not implemented');
    }
  };

  // Handle export
  const handleExport = () => {
    if (onExport) {
      onExport(currentRun.id);
    } else {
      // Default export implementation - show export options
      setShowExportOptions(true);
    }
  };
  
  // Handle archive
  const handleArchive = () => {
    setConfirmationModal({
      isOpen: true,
      itemId: currentRun.id,
      newStatus: 'completed', // Not used for archiving
      title: currentRun.archived ? 'Unarchive Run' : 'Archive Run',
      message: currentRun.archived 
        ? 'Are you sure you want to unarchive this run? It will appear in the default run history view.'
        : 'Are you sure you want to archive this run? It will be hidden from the default run history view.'
    });
  };
  
  // Handle archive confirmation
  const handleConfirmArchive = async () => {
    try {
      setIsLoading(true);
      
      // Call API to archive/unarchive run
      // const agentService = AgentService.getInstance();
      // await agentService.archiveRun(currentRun.id, !currentRun.archived);
      
      // For now, we'll just update the local state
      const updatedRun = { 
        ...currentRun, 
        archived: !currentRun.archived,
        archivedAt: !currentRun.archived ? new Date().toISOString() : undefined,
        archivedBy: !currentRun.archived ? 'Current User' : undefined
      };
      
      setRefreshedRun(updatedRun);
      
      // Show success message
      showToast('success', `Run ${updatedRun.archived ? 'archived' : 'unarchived'} successfully`);
    } catch (error) {
      console.error('Failed to archive/unarchive run:', error);
      showToast('error', 'Failed to archive/unarchive run');
    } finally {
      setIsLoading(false);
      setConfirmationModal(prev => ({ ...prev, isOpen: false }));
    }
  };
  
  // State for export options modal
  const [showExportOptions, setShowExportOptions] = useState(false);
  
  // Handle action item status change
  const handleActionItemStatusChange = (itemId: string, newStatus: 'completed' | 'ignored' | 'pending') => {
    // Show confirmation modal with appropriate message
    const title = newStatus === 'completed' ? 'Complete Action Item' :
                 newStatus === 'ignored' ? 'Ignore Action Item' : 'Reset Action Item';
    
    const message = newStatus === 'completed' ? 'Are you sure you want to mark this action item as completed?' :
                   newStatus === 'ignored' ? 'Are you sure you want to ignore this action item?' :
                   'Are you sure you want to reset this action item to pending?';
    
    setConfirmationModal({
      isOpen: true,
      itemId,
      newStatus,
      title,
      message
    });
  };
  
  // Handle confirmation of action item status change or archive
  const handleConfirmStatusChange = async () => {
    const { itemId, newStatus } = confirmationModal;
    
    // Check if this is an archive confirmation
    if (itemId === currentRun.id) {
      await handleConfirmArchive();
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Call API to update action item status
      const agentService = AgentService.getInstance();
      
      // This would be the actual API call in a real implementation
      // await agentService.updateActionItemStatus(currentRun.id, itemId, newStatus);
      
      // For now, we'll just update the local state
      if (refreshedRun) {
        const updatedRun = { ...refreshedRun };
        if (updatedRun.results?.actionItems) {
          updatedRun.results.actionItems = updatedRun.results.actionItems.map(item => 
            item.id === itemId ? { ...item, status: newStatus } : item
          );
          setRefreshedRun(updatedRun);
        }
      } else {
        const updatedRun = { ...currentRun };
        if (updatedRun.results?.actionItems) {
          updatedRun.results.actionItems = updatedRun.results.actionItems.map(item => 
            item.id === itemId ? { ...item, status: newStatus } : item
          );
          setRefreshedRun(updatedRun);
        }
      }
      
      // Show success message
      showToast('success', `Action item ${newStatus === 'completed' ? 'completed' : 
                            newStatus === 'ignored' ? 'ignored' : 'reset to pending'} successfully`);
    } catch (error) {
      console.error('Failed to update action item status:', error);
      showToast('error', 'Failed to update action item status');
    } finally {
      setIsLoading(false);
      setConfirmationModal(prev => ({ ...prev, isOpen: false }));
    }
  };
  
  // Import export utilities
  const { 
    convertRunToCSV, 
    downloadFile, 
    generateShareableLink, 
    copyToClipboard 
  } = require('../../../utils/exportUtils');
  
  // Handle export to JSON
  const handleExportToJSON = () => {
    const data = JSON.stringify(currentRun, null, 2);
    downloadFile(data, `run-${currentRun.id}.json`, 'application/json');
    setShowExportOptions(false);
    showToast('success', 'Run data exported as JSON');
  };
  
  // Handle export to CSV
  const handleExportToCSV = () => {
    const csv = convertRunToCSV(currentRun);
    downloadFile(csv, `run-${currentRun.id}.csv`, 'text/csv');
    setShowExportOptions(false);
    showToast('success', 'Run data exported as CSV');
  };
  
  // Handle share link generation
  const handleShareLink = async () => {
    const shareableLink = generateShareableLink(currentRun.id);
    const copied = await copyToClipboard(shareableLink);
    
    if (copied) {
      showToast('success', 'Shareable link copied to clipboard');
    } else {
      showToast('error', 'Failed to copy link to clipboard');
    }
    
    setShowExportOptions(false);
  };

  return (
    <div className="p-4">
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h3 className="text-lg font-medium text-gray-900">
              {run.agentType}
            </h3>
            {currentRun.archived && (
              <span className="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                Archived
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleArchive}
              className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
            >
              {currentRun.archived ? 'Unarchive' : 'Archive'}
            </button>
            <span className={`px-2 py-1 ${getStatusBadgeClasses(run.status)} rounded-full text-sm`}>
              {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
            </span>
          </div>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Run ID: {run.id}
        </p>
        {currentRun.archived && (
          <p className="mt-1 text-xs text-gray-500">
            Archived on {new Date(currentRun.archivedAt || '').toLocaleString()} by {currentRun.archivedBy || 'Unknown'}
          </p>
        )}
        <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Start Time</p>
            <p className="font-medium">{run.startTime ? new Date(run.startTime).toLocaleString() : 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-500">End Time</p>
            <p className="font-medium">{run.endTime ? new Date(run.endTime).toLocaleString() : 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-500">Duration</p>
            <p className="font-medium">{calculateDuration(run.startTime, run.endTime)}</p>
          </div>
          <div>
            <p className="text-gray-500">Progress</p>
            <div className="flex items-center">
              <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                <div 
                  className={`h-2 rounded-full ${
                    run.status === 'failed' ? 'bg-red-600' : 
                    run.status === 'completed' ? 'bg-green-600' : 'bg-blue-600'
                  }`}
                  style={{width: `${run.progress}%`}}
                ></div>
              </div>
              <span className="text-xs font-medium">{run.progress}%</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-4">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button 
              className={`${activeTab === 'details' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('details')}
            >
              Details
            </button>
            <button 
              className={`${activeTab === 'thinking' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('thinking')}
            >
              Thinking Process
            </button>
            <button 
              className={`${activeTab === 'config' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('config')}
            >
              Configuration
            </button>
            <button 
              className={`${activeTab === 'results' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('results')}
            >
              Results
            </button>
          </nav>
        </div>
        
        <div className="mt-4">
          {activeTab === 'details' && (
            <>
              <h4 className="text-sm font-medium text-gray-900">Run Details</h4>
              <div className="mt-2 bg-gray-50 p-4 rounded-md">
                {isLoading ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <p className="text-gray-500">Agent Type</p>
                        <p className="font-medium">{currentRun.agentType}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Status</p>
                        <p className="font-medium">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClasses(currentRun.status)}`}>
                            {currentRun.status.charAt(0).toUpperCase() + currentRun.status.slice(1)}
                          </span>
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Run ID</p>
                        <p className="font-medium text-xs">{currentRun.id}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Progress</p>
                        <div className="flex items-center">
                          <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className={`h-2 rounded-full ${
                                currentRun.status === 'failed' ? 'bg-red-600' : 
                                currentRun.status === 'completed' ? 'bg-green-600' : 'bg-blue-600'
                              }`}
                              style={{width: `${currentRun.progress}%`}}
                            ></div>
                          </div>
                          <span className="text-xs font-medium">{currentRun.progress}%</span>
                        </div>
                      </div>
                      <div>
                        <p className="text-gray-500">Start Time</p>
                        <p className="font-medium">{currentRun.startTime ? new Date(currentRun.startTime).toLocaleString() : 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">End Time</p>
                        <p className="font-medium">{currentRun.endTime ? new Date(currentRun.endTime).toLocaleString() : 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Duration</p>
                        <p className="font-medium">{calculateDuration(currentRun.startTime, currentRun.endTime)}</p>
                      </div>
                      {currentRun.metrics && (
                        <div>
                          <p className="text-gray-500">Resource Usage</p>
                          <div className="flex space-x-2">
                            {currentRun.metrics.resourceUsage?.cpu !== undefined && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                CPU: {(currentRun.metrics.resourceUsage.cpu * 100).toFixed(1)}%
                              </span>
                            )}
                            {currentRun.metrics.resourceUsage?.memory !== undefined && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Memory: {currentRun.metrics.resourceUsage.memory} MB
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {currentRun.error && (
                      <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Error</h3>
                            <div className="mt-2 text-sm text-red-700">
                              <p>{currentRun.error}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {currentRun.results && (
                      <div className="mb-4 bg-green-50 border-l-4 border-green-400 p-4">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-green-800">Summary</h3>
                            <div className="mt-2 text-sm text-green-700">
                              <p>{currentRun.results.summary}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Additional metrics */}
                    {currentRun.metrics && Object.keys(currentRun.metrics).filter(key => key !== 'resourceUsage' && key !== 'duration').length > 0 && (
                      <div className="mb-4">
                        <h5 className="text-sm font-medium text-gray-900 mb-2">Additional Metrics</h5>
                        <div className="grid grid-cols-2 gap-4">
                          {Object.entries(currentRun.metrics)
                            .filter(([key]) => key !== 'resourceUsage' && key !== 'duration')
                            .map(([key, value]) => (
                              <div key={key} className="bg-white p-3 rounded-md shadow-sm">
                                <p className="text-xs text-gray-500">{key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}</p>
                                <p className="text-sm font-medium">
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </p>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                    
                    <details className="mt-4">
                      <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                        View Raw Run Data
                      </summary>
                      <pre className="mt-2 text-xs overflow-auto max-h-96 bg-gray-100 p-2 rounded">
                        {JSON.stringify(currentRun, null, 2)}
                      </pre>
                    </details>
                  </>
                )}
              </div>
            </>
          )}
          
          {activeTab === 'thinking' && (
            <>
              <h4 className="text-sm font-medium text-gray-900">Thinking Process</h4>
              <div className="mt-2">
                <ThinkingProcessContainer 
                  runId={currentRun.id} 
                  autoScroll={false} 
                />
              </div>
            </>
          )}
          
          {activeTab === 'config' && (
            <>
              <h4 className="text-sm font-medium text-gray-900">Configuration</h4>
              <div className="mt-2 bg-gray-50 p-4 rounded-md">
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Agent Parameters</h5>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Agent Type</p>
                      <p className="font-medium">{currentRun.config.agentType}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Matching Threshold</p>
                      <p className="font-medium">{currentRun.config.parameters.matchingThreshold || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Numeric Tolerance</p>
                      <p className="font-medium">{currentRun.config.parameters.numericTolerance || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Report Bucket</p>
                      <p className="font-medium">{currentRun.config.parameters.reportBucket || 'N/A'}</p>
                    </div>
                    {/* Display any additional parameters */}
                    {Object.entries(currentRun.config.parameters)
                      .filter(([key]) => !['matchingThreshold', 'numericTolerance', 'reportBucket'].includes(key))
                      .map(([key, value]) => (
                        <div key={key}>
                          <p className="text-gray-500">{key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}</p>
                          <p className="font-medium">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</p>
                        </div>
                      ))}
                  </div>
                </div>
                
                {currentRun.config.inputData && Object.keys(currentRun.config.inputData).length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-sm font-medium text-gray-900 mb-2">Input Data</h5>
                    <div className="bg-white p-3 rounded-md shadow-sm">
                      {currentRun.config.inputData.tradeIds && currentRun.config.inputData.tradeIds.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500">Trade IDs</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {currentRun.config.inputData.tradeIds.map((id, index) => (
                              <a 
                                key={index} 
                                href={`/trades?id=${id}`}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
                              >
                                {id}
                                <svg className="ml-1 h-3 w-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M5.22 14.78a.75.75 0 001.06 0l7.22-7.22v5.69a.75.75 0 001.5 0v-7.5a.75.75 0 00-.75-.75h-7.5a.75.75 0 000 1.5h5.69l-7.22 7.22a.75.75 0 000 1.06z" clipRule="evenodd" />
                                </svg>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {currentRun.config.inputData.documentIds && currentRun.config.inputData.documentIds.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500">Document IDs</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {currentRun.config.inputData.documentIds.map((id, index) => (
                              <a 
                                key={index} 
                                href={`/upload?view=${id}`}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 hover:bg-purple-200 transition-colors"
                              >
                                {id}
                                <svg className="ml-1 h-3 w-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M5.22 14.78a.75.75 0 001.06 0l7.22-7.22v5.69a.75.75 0 001.5 0v-7.5a.75.75 0 00-.75-.75h-7.5a.75.75 0 000 1.5h5.69l-7.22 7.22a.75.75 0 000 1.06z" clipRule="evenodd" />
                                </svg>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {currentRun.config.inputData.dateRange && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500">Date Range</p>
                          <p className="text-sm font-medium">
                            {new Date(currentRun.config.inputData.dateRange.startDate).toLocaleDateString()} - {new Date(currentRun.config.inputData.dateRange.endDate).toLocaleDateString()}
                          </p>
                        </div>
                      )}
                      
                      {/* Display any additional input data */}
                      {Object.entries(currentRun.config.inputData)
                        .filter(([key]) => !['tradeIds', 'documentIds', 'dateRange'].includes(key))
                        .map(([key, value]) => (
                          <div key={key} className="mb-3">
                            <p className="text-xs text-gray-500">{key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}</p>
                            <p className="text-sm font-medium">
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </p>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
                
                <details className="mt-4">
                  <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                    View Raw Configuration Data
                  </summary>
                  <pre className="mt-2 text-xs overflow-auto max-h-96 bg-gray-100 p-2 rounded">
                    {JSON.stringify(currentRun.config, null, 2)}
                  </pre>
                </details>
              </div>
            </>
          )}
          
          {activeTab === 'results' && (
            <>
              <h4 className="text-sm font-medium text-gray-900">Results</h4>
              <div className="mt-2 bg-gray-50 p-4 rounded-md">
                {currentRun.results ? (
                  <>
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-900">Summary</p>
                      <p className="text-sm text-gray-700">{currentRun.results.summary}</p>
                    </div>
                    
                    {/* Related Data Section */}
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-900">Related Data</p>
                      <div className="mt-2 bg-white p-3 rounded-md shadow-sm">
                        {/* Related Trades */}
                        {currentRun.config.inputData?.tradeIds && currentRun.config.inputData.tradeIds.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs text-gray-500">Related Trades</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {currentRun.config.inputData.tradeIds.map((id, index) => (
                                <a 
                                  key={index} 
                                  href={`/trades?id=${id}`}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
                                >
                                  {id}
                                  <svg className="ml-1 h-3 w-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M5.22 14.78a.75.75 0 001.06 0l7.22-7.22v5.69a.75.75 0 001.5 0v-7.5a.75.75 0 00-.75-.75h-7.5a.75.75 0 000 1.5h5.69l-7.22 7.22a.75.75 0 000 1.06z" clipRule="evenodd" />
                                  </svg>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Related Documents */}
                        {currentRun.config.inputData?.documentIds && currentRun.config.inputData.documentIds.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs text-gray-500">Related Documents</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {currentRun.config.inputData.documentIds.map((id, index) => (
                                <a 
                                  key={index} 
                                  href={`/upload?view=${id}`}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 hover:bg-purple-200 transition-colors"
                                >
                                  {id}
                                  <svg className="ml-1 h-3 w-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M5.22 14.78a.75.75 0 001.06 0l7.22-7.22v5.69a.75.75 0 001.5 0v-7.5a.75.75 0 00-.75-.75h-7.5a.75.75 0 000 1.5h5.69l-7.22 7.22a.75.75 0 000 1.06z" clipRule="evenodd" />
                                  </svg>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* If there are no related trades or documents */}
                        {(!currentRun.config.inputData?.tradeIds || currentRun.config.inputData.tradeIds.length === 0) && 
                         (!currentRun.config.inputData?.documentIds || currentRun.config.inputData.documentIds.length === 0) && (
                          <p className="text-sm text-gray-500">No related trades or documents found.</p>
                        )}
                      </div>
                    </div>
                    
                    {currentRun.results.generatedReports && currentRun.results.generatedReports.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-900">Generated Reports</p>
                        <ul className="mt-2 divide-y divide-gray-200">
                          {currentRun.results.generatedReports.map((report) => (
                            <li key={report.id} className="py-2">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{report.name}</p>
                                  <p className="text-xs text-gray-500">{report.type}</p>
                                </div>
                                <a
                                  href={report.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-blue-600 hover:text-blue-800"
                                >
                                  Download
                                </a>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {currentRun.results.actionItems && currentRun.results.actionItems.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-900">Action Items</p>
                        <ul className="mt-2 divide-y divide-gray-200">
                          {currentRun.results.actionItems.map((item) => (
                            <li key={item.id} className="py-3">
                              <div className="flex items-start justify-between">
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{item.description}</p>
                                  <p className="text-xs text-gray-500 mb-2">{item.type}</p>
                                  
                                  {/* Action buttons */}
                                  <div className="flex space-x-2 mt-1">
                                    {item.status === 'pending' && (
                                      <>
                                        <button
                                          onClick={() => handleActionItemStatusChange(item.id, 'completed')}
                                          className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                                        >
                                          Complete
                                        </button>
                                        <button
                                          onClick={() => handleActionItemStatusChange(item.id, 'ignored')}
                                          className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                        >
                                          Ignore
                                        </button>
                                      </>
                                    )}
                                    {item.status !== 'pending' && (
                                      <button
                                        onClick={() => handleActionItemStatusChange(item.id, 'pending')}
                                        className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                      >
                                        Reset
                                      </button>
                                    )}
                                  </div>
                                </div>
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                  item.status === 'completed' ? 'bg-green-100 text-green-800' :
                                  item.status === 'ignored' ? 'bg-gray-100 text-gray-800' :
                                  'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                                </span>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* Output data visualization */}
                    {currentRun.results.outputData && Object.keys(currentRun.results.outputData).length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-900">Output Data</p>
                        <div className="mt-2 grid grid-cols-2 gap-4">
                          {Object.entries(currentRun.results.outputData).map(([key, value]) => (
                            <div key={key} className="bg-white p-3 rounded-md shadow-sm">
                              <p className="text-xs text-gray-500">{key}</p>
                              <p className="text-sm font-medium">
                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <details className="mt-4">
                      <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                        View Raw Results Data
                      </summary>
                      <pre className="mt-2 text-xs overflow-auto max-h-96 bg-gray-100 p-2 rounded">
                        {JSON.stringify(currentRun.results, null, 2)}
                      </pre>
                    </details>
                  </>
                ) : (
                  <div className="text-center py-8">
                    {(['running', 'queued'] as AgentRunStatus[]).includes(currentRun.status) ? (
                      <>
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-sm text-gray-500">
                          Run is still in progress. Results will be available when the run completes.
                        </p>
                      </>
                    ) : currentRun.error ? (
                      <div className="bg-red-50 border-l-4 border-red-400 p-4">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <p className="text-sm text-red-700">
                              {currentRun.error}
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">
                        No results available for this run.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Export Options Modal */}
      {showExportOptions && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Export Options</h3>
              <button
                onClick={() => setShowExportOptions(false)}
                className="text-gray-400 hover:text-gray-500"
                aria-label="Close"
              >
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <button
                onClick={handleExportToJSON}
                className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
              >
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-gray-400 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-900">Export as JSON</span>
                </div>
                <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              
              <button
                onClick={handleExportToCSV}
                className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
              >
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-gray-400 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-900">Export as CSV</span>
                </div>
                <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              
              <button
                onClick={handleShareLink}
                className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
              >
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-gray-400 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-900">Share Link</span>
                </div>
                <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Action Item Confirmation Modal */}
      {confirmationModal.isOpen && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">{confirmationModal.title}</h3>
              <button
                onClick={() => setConfirmationModal(prev => ({ ...prev, isOpen: false }))}
                className="text-gray-400 hover:text-gray-500"
                aria-label="Close"
              >
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <p className="text-sm text-gray-500 mb-4">{confirmationModal.message}</p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setConfirmationModal(prev => ({ ...prev, isOpen: false }))}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmStatusChange}
                className={`px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  confirmationModal.newStatus === 'completed' ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500' :
                  confirmationModal.newStatus === 'ignored' ? 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500' :
                  'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                }`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </span>
                ) : (
                  'Confirm'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RunDetailView;