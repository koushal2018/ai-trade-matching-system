import React, { useState } from 'react';
import { AgentRun } from '../../../types/agent';
import { useToast } from '../../../context/ToastContext';
import { 
  convertRunsToComparisonCSV, 
  downloadFile, 
  generateShareableLink, 
  copyToClipboard 
} from '../../../utils/exportUtils';

interface RunComparisonViewProps {
  runs: AgentRun[];
  onClose: () => void;
}

const RunComparisonView: React.FC<RunComparisonViewProps> = ({ runs, onClose }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'config' | 'results' | 'metrics'>('config');
  const [showExportOptions, setShowExportOptions] = useState(false);

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

  // Get all unique parameter keys from all runs
  const getAllParameterKeys = () => {
    const keys = new Set<string>();
    runs.forEach(run => {
      Object.keys(run.config.parameters).forEach(key => keys.add(key));
    });
    return Array.from(keys);
  };

  // Get all unique output data keys from all runs
  const getAllOutputDataKeys = () => {
    const keys = new Set<string>();
    runs.forEach(run => {
      if (run.results?.outputData) {
        Object.keys(run.results.outputData).forEach(key => keys.add(key));
      }
    });
    return Array.from(keys);
  };

  // Get all unique metric keys from all runs
  const getAllMetricKeys = () => {
    const keys = new Set<string>();
    runs.forEach(run => {
      if (run.metrics) {
        Object.keys(run.metrics).forEach(key => {
          if (key !== 'resourceUsage') {
            keys.add(key);
          }
        });
      }
    });
    return Array.from(keys);
  };

  // Format key for display
  const formatKey = (key: string): string => {
    return key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1');
  };

  // Format value for display
  const formatValue = (value: any): string => {
    if (value === undefined || value === null) return 'N/A';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  // Handle export to JSON
  const handleExportToJSON = () => {
    const data = JSON.stringify(runs, null, 2);
    downloadFile(data, `run-comparison-${runs.map(r => r.id.slice(0, 4)).join('-')}.json`, 'application/json');
    setShowExportOptions(false);
    showToast('success', 'Comparison data exported as JSON');
  };
  
  // Handle export to CSV
  const handleExportToCSV = () => {
    const csv = convertRunsToComparisonCSV(runs);
    downloadFile(csv, `run-comparison-${runs.map(r => r.id.slice(0, 4)).join('-')}.csv`, 'text/csv');
    setShowExportOptions(false);
    showToast('success', 'Comparison data exported as CSV');
  };
  
  // Handle share link generation
  const handleShareLink = async () => {
    // Create a shareable link with multiple run IDs
    const runIds = runs.map(run => run.id).join(',');
    const shareableLink = generateShareableLink(runIds);
    const copied = await copyToClipboard(shareableLink);
    
    if (copied) {
      showToast('success', 'Shareable link copied to clipboard');
    } else {
      showToast('error', 'Failed to copy link to clipboard');
    }
    
    setShowExportOptions(false);
  };

  return (
    <div className="bg-white shadow sm:rounded-md p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Run Comparison</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowExportOptions(true)}
            className="text-gray-400 hover:text-gray-500"
            aria-label="Export"
          >
            <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
            aria-label="Close"
          >
            <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Export Options Modal */}
      {showExportOptions && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Export Comparison</h3>
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
                  <span className="text-sm font-medium text-gray-900">Generate Shareable Link</span>
                </div>
                <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mb-4">
        <div className="flex flex-wrap">
          {runs.map((run, index) => (
            <div key={run.id} className="mr-2 mb-2 px-3 py-1 bg-blue-50 rounded-full text-sm flex items-center">
              <span className="font-medium text-blue-800">{run.agentType}</span>
              <span className={`ml-2 px-2 py-0.5 ${getStatusBadgeClasses(run.status)} rounded-full text-xs`}>
                {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
              </span>
              <span className="ml-2 text-xs text-gray-500">
                {run.startTime ? new Date(run.startTime).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="border-b border-gray-200 mb-4">
        <nav className="-mb-px flex space-x-8">
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
          <button 
            className={`${activeTab === 'metrics' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
            onClick={() => setActiveTab('metrics')}
          >
            Metrics
          </button>
        </nav>
      </div>

      {activeTab === 'config' && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parameter
                </th>
                {runs.map((run, index) => (
                  <th key={run.id} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run {index + 1}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Agent Type
                </td>
                {runs.map(run => (
                  <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {run.agentType}
                  </td>
                ))}
              </tr>
              {getAllParameterKeys().map(key => (
                <tr key={key}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatKey(key)}
                  </td>
                  {runs.map(run => (
                    <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatValue(run.config.parameters[key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'results' && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Result
                </th>
                {runs.map((run, index) => (
                  <th key={run.id} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run {index + 1}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Status
                </td>
                {runs.map(run => (
                  <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 ${getStatusBadgeClasses(run.status)} rounded-full text-xs`}>
                      {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
                    </span>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Summary
                </td>
                {runs.map(run => (
                  <td key={run.id} className="px-6 py-4 text-sm text-gray-500">
                    {run.results?.summary || 'N/A'}
                  </td>
                ))}
              </tr>
              {getAllOutputDataKeys().map(key => (
                <tr key={key}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatKey(key)}
                  </td>
                  {runs.map(run => (
                    <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatValue(run.results?.outputData?.[key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'metrics' && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Metric
                </th>
                {runs.map((run, index) => (
                  <th key={run.id} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run {index + 1}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Duration
                </td>
                {runs.map(run => (
                  <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {calculateDuration(run.startTime, run.endTime)}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  CPU Usage
                </td>
                {runs.map(run => (
                  <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {run.metrics?.resourceUsage?.cpu !== undefined 
                      ? `${(run.metrics.resourceUsage.cpu * 100).toFixed(1)}%` 
                      : 'N/A'}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Memory Usage
                </td>
                {runs.map(run => (
                  <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {run.metrics?.resourceUsage?.memory !== undefined 
                      ? `${run.metrics.resourceUsage.memory} MB` 
                      : 'N/A'}
                  </td>
                ))}
              </tr>
              {getAllMetricKeys().map(key => (
                <tr key={key}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatKey(key)}
                  </td>
                  {runs.map(run => (
                    <td key={run.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatValue(run.metrics?.[key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default RunComparisonView;