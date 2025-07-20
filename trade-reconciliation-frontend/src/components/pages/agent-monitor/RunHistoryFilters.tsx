import React, { useState } from 'react';
import { AgentRunStatus } from '../../../types/agent';

interface RunHistoryFiltersProps {
  onFilterChange: (filters: {
    agentType?: string;
    status?: AgentRunStatus;
    startDate?: string;
    endDate?: string;
    sortBy?: string;
    sortDirection?: 'asc' | 'desc';
    showArchived?: boolean;
  }) => void;
  onReset: () => void;
}

const RunHistoryFilters: React.FC<RunHistoryFiltersProps> = ({ onFilterChange, onReset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [agentType, setAgentType] = useState<string>('');
  const [status, setStatus] = useState<AgentRunStatus | ''>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('startTime');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [showArchived, setShowArchived] = useState<boolean>(false);

  const handleApplyFilters = () => {
    const filters: any = {};
    
    if (agentType) filters.agentType = agentType;
    if (status) filters.status = status;
    if (startDate) filters.startDate = startDate;
    if (endDate) filters.endDate = endDate;
    if (sortBy) filters.sortBy = sortBy;
    if (sortDirection) filters.sortDirection = sortDirection;
    filters.showArchived = showArchived;
    
    onFilterChange(filters);
  };

  const handleReset = () => {
    setAgentType('');
    setStatus('');
    setStartDate('');
    setEndDate('');
    setSortBy('startTime');
    setSortDirection('desc');
    setShowArchived(false);
    onReset();
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-4">
      <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-sm font-medium text-gray-700">Filter History</h3>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {isExpanded ? 'Hide Filters' : 'Show Filters'}
        </button>
      </div>
      
      {isExpanded && (
        <div className="px-4 py-4 sm:p-6">
          <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
            <div className="sm:col-span-2">
              <label htmlFor="agent-type" className="block text-sm font-medium text-gray-700">
                Agent Type
              </label>
              <select
                id="agent-type"
                name="agent-type"
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                value={agentType}
                onChange={(e) => setAgentType(e.target.value)}
              >
                <option value="">All Types</option>
                <option value="trade-pdf-processing">Trade PDF Processing</option>
                <option value="trade-matching">Trade Matching</option>
                <option value="reconciliation">Reconciliation</option>
              </select>
            </div>
            
            <div className="sm:col-span-2">
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                Status
              </label>
              <select
                id="status"
                name="status"
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                value={status}
                onChange={(e) => setStatus(e.target.value as AgentRunStatus | '')}
              >
                <option value="">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <div className="mt-2">
                <div className="flex items-center">
                  <input
                    id="show-archived"
                    name="show-archived"
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    checked={showArchived}
                    onChange={(e) => setShowArchived(e.target.checked)}
                  />
                  <label htmlFor="show-archived" className="ml-2 block text-sm text-gray-700">
                    Include archived runs
                  </label>
                </div>
              </div>
            </div>
            
            <div className="sm:col-span-2">
              <label htmlFor="sort-by" className="block text-sm font-medium text-gray-700">
                Sort By
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <select
                  id="sort-by"
                  name="sort-by"
                  className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-l-md"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <option value="startTime">Start Time</option>
                  <option value="endTime">End Time</option>
                  <option value="agentType">Agent Type</option>
                  <option value="status">Status</option>
                </select>
                <button
                  type="button"
                  className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm"
                  onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
                >
                  {sortDirection === 'asc' ? (
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            
            <div className="sm:col-span-3">
              <label htmlFor="start-date" className="block text-sm font-medium text-gray-700">
                Start Date
              </label>
              <input
                type="date"
                name="start-date"
                id="start-date"
                className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            
            <div className="sm:col-span-3">
              <label htmlFor="end-date" className="block text-sm font-medium text-gray-700">
                End Date
              </label>
              <input
                type="date"
                name="end-date"
                id="end-date"
                className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          
          <div className="mt-5 flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Reset
            </button>
            <button
              type="button"
              onClick={handleApplyFilters}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RunHistoryFilters;