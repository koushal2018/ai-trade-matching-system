import React, { useState } from 'react';
import { AgentThinkingStepType } from '../../../types/agent';
import { ThinkingProcessService } from '../../../services/agent/ThinkingProcessService';

interface ThinkingProcessFiltersProps {
  onSearch: (query: string) => void;
  onFilterChange: (types: AgentThinkingStepType[]) => void;
  onTimeRangeChange?: (startTime: string, endTime: string) => void;
  selectedTypes: AgentThinkingStepType[];
  searchQuery: string;
}

const ThinkingProcessFilters: React.FC<ThinkingProcessFiltersProps> = ({
  onSearch,
  onFilterChange,
  onTimeRangeChange,
  selectedTypes,
  searchQuery,
}) => {
  const [isAdvancedFiltersOpen, setIsAdvancedFiltersOpen] = useState(false);
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  // Filter types
  const filterTypes: { type: AgentThinkingStepType; label: string; icon: string }[] = [
    { type: 'action', label: 'Actions', icon: 'play' },
    { type: 'decision', label: 'Decisions', icon: 'lightbulb' },
    { type: 'observation', label: 'Observations', icon: 'eye' },
    { type: 'error', label: 'Errors', icon: 'exclamation-triangle' },
    { type: 'info', label: 'Info', icon: 'info-circle' },
  ];

  // Handle filter change
  const handleFilterChange = (type: AgentThinkingStepType) => {
    let newSelectedTypes: AgentThinkingStepType[];
    
    if (selectedTypes.includes(type)) {
      newSelectedTypes = selectedTypes.filter(t => t !== type);
    } else {
      newSelectedTypes = [...selectedTypes, type];
    }
    
    onFilterChange(newSelectedTypes);
  };

  // Handle time range change
  const handleTimeRangeApply = () => {
    if (onTimeRangeChange && startTime && endTime) {
      onTimeRangeChange(startTime, endTime);
    }
  };

  // Handle clear all filters
  const handleClearFilters = () => {
    onSearch('');
    onFilterChange([]);
    setStartTime('');
    setEndTime('');
    if (onTimeRangeChange) {
      onTimeRangeChange('', '');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0 sm:space-x-4">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search thinking process..."
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className="h-5 w-5 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setIsAdvancedFiltersOpen(!isAdvancedFiltersOpen)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg
              className="h-4 w-4 mr-2 text-gray-500"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z"
                clipRule="evenodd"
              />
            </svg>
            {isAdvancedFiltersOpen ? 'Hide Filters' : 'Show Filters'}
          </button>
          
          {(selectedTypes.length > 0 || searchQuery || startTime || endTime) && (
            <button
              type="button"
              onClick={handleClearFilters}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>
      
      {isAdvancedFiltersOpen && (
        <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Filter by Type</h4>
              <div className="flex flex-wrap gap-2">
                {filterTypes.map(({ type, label }) => (
                  <button
                    key={type}
                    onClick={() => handleFilterChange(type)}
                    className={`px-3 py-1 text-xs font-medium rounded-full ${
                      selectedTypes.includes(type)
                        ? ThinkingProcessService.getStepTypeClass(type)
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            
            {onTimeRangeChange && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Filter by Time Range</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="start-time" className="block text-xs font-medium text-gray-500">
                      Start Time
                    </label>
                    <input
                      type="datetime-local"
                      id="start-time"
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="end-time" className="block text-xs font-medium text-gray-500">
                      End Time
                    </label>
                    <input
                      type="datetime-local"
                      id="end-time"
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                </div>
                <div className="mt-2 flex justify-end">
                  <button
                    type="button"
                    onClick={handleTimeRangeApply}
                    disabled={!startTime || !endTime}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Apply Time Range
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ThinkingProcessFilters;