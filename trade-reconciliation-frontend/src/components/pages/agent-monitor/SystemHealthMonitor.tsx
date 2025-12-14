import React, { useEffect, useState } from 'react';
import { AgentService } from '../../../services/agent/AgentService';
import { SystemHealth } from '../../../types/agent';
import { SystemHealthService } from '../../../services/agent/SystemHealthService';

interface SystemHealthMonitorProps {
  refreshInterval?: number; // in milliseconds
}

const SystemHealthMonitor: React.FC<SystemHealthMonitorProps> = ({ 
  refreshInterval = 30000 // Default to 30 seconds
}) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch system health data
  const fetchSystemHealth = async () => {
    try {
      const agentService = AgentService.getInstance();
      const healthData = await agentService.getSystemHealth();
      setHealth(healthData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch system health data');
      console.error('Error fetching system health:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Initial fetch and set up interval for refreshing
  useEffect(() => {
    fetchSystemHealth();
    
    // Set up interval for refreshing data
    const intervalId = setInterval(fetchSystemHealth, refreshInterval);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, [refreshInterval]);
  
  // Format memory usage for display
  const formatMemoryUsage = (memoryPercentage: number): string => {
    // This is a simplified example - in a real app, you would get actual memory values
    const totalMemory = 8; // GB
    const usedMemory = (memoryPercentage / 100) * totalMemory;
    return `${usedMemory.toFixed(1)} GB / ${totalMemory} GB`;
  };
  
  // Determine CSS class for resource usage bars
  const getResourceClass = (usage: number): string => {
    return SystemHealthService.getResourceUsageClass(usage);
  };
  
  // Determine CSS class for status badges
  const getStatusClass = (status: 'healthy' | 'degraded' | 'unhealthy'): string => {
    return SystemHealthService.getStatusClass(status);
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error || !health) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">System Health Error</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error || 'Failed to load system health data'}</p>
            </div>
            <div className="mt-4">
              <button
                type="button"
                onClick={fetchSystemHealth}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // Check if there are any critical issues
  const hasCriticalIssues = SystemHealthService.isCritical(health);
  
  return (
    <div className="space-y-6">
      {/* Overall System Status */}
      {hasCriticalIssues && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Critical System Alert</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>System resources are critically low. Consider stopping non-essential agent runs.</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Resource Usage Metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        {/* CPU Usage */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 rounded-md p-3 ${getResourceClass(health.metrics.cpu)}`}>
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    CPU Usage
                  </dt>
                  <dd>
                    <div className="text-lg font-medium text-gray-900">
                      {health.metrics.cpu}%
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-4">
              <div className="relative pt-1">
                <div className="overflow-hidden h-2 mb-1 text-xs flex rounded bg-gray-200">
                  <div 
                    style={{ width: `${health.metrics.cpu}%` }} 
                    className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${getResourceClass(health.metrics.cpu)}`}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Memory Usage */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 rounded-md p-3 ${getResourceClass(health.metrics.memory)}`}>
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Memory Usage
                  </dt>
                  <dd>
                    <div className="text-lg font-medium text-gray-900">
                      {formatMemoryUsage(health.metrics.memory)}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-4">
              <div className="relative pt-1">
                <div className="overflow-hidden h-2 mb-1 text-xs flex rounded bg-gray-200">
                  <div 
                    style={{ width: `${health.metrics.memory}%` }} 
                    className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${getResourceClass(health.metrics.memory)}`}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Uptime */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Uptime
                  </dt>
                  <dd>
                    <div className="text-lg font-medium text-gray-900">
                      {SystemHealthService.formatUptime(health.metrics.uptime)}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Last updated: {new Date(health.timestamp).toLocaleString()}
            </div>
          </div>
        </div>
      </div>
      
      {/* Agent Health Status */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-900">Agent Health</h4>
        <div className="mt-2 grid grid-cols-1 gap-5 sm:grid-cols-3">
          {Object.entries(health.agents).map(([agentType, agentHealth]) => (
            <div key={agentType} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between">
                  <h5 className="text-sm font-medium text-gray-900">{agentType}</h5>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusClass(agentHealth.status)}`}>
                    {agentHealth.status.charAt(0).toUpperCase() + agentHealth.status.slice(1)}
                  </span>
                </div>
                <div className="mt-2 text-sm text-gray-500">
                  {agentHealth.lastRun && (
                    <div>Last run: {new Date(agentHealth.lastRun).toLocaleString()}</div>
                  )}
                  {agentHealth.message && (
                    <div className="mt-1">{agentHealth.message}</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Resource Alerts */}
      {health.metrics.cpu > 80 || health.metrics.memory > 80 || health.metrics.disk > 80 ? (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900">Resource Alerts</h4>
          <div className="mt-2 space-y-4">
            {health.metrics.cpu > 80 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      High CPU usage detected ({health.metrics.cpu}%). Consider limiting concurrent agent runs.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {health.metrics.memory > 80 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      High memory usage detected ({health.metrics.memory}%). Some operations may be slower than usual.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {health.metrics.disk > 80 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      Low disk space ({health.metrics.disk}% used). Consider cleaning up old reports and logs.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
      
      {/* Refresh Button */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={fetchSystemHealth}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>
    </div>
  );
};

export default SystemHealthMonitor;