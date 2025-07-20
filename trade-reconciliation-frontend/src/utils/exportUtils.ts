/**
 * Utilities for exporting and sharing agent run data
 */

import { AgentRun } from '../types/agent';

/**
 * Converts an agent run to CSV format
 */
export const convertRunToCSV = (run: AgentRun): string => {
  // Start with the basic run info
  let csv = 'Property,Value\n';
  csv += `ID,${run.id}\n`;
  csv += `Agent Type,${run.agentType}\n`;
  csv += `Status,${run.status}\n`;
  csv += `Progress,${run.progress}%\n`;
  csv += `Start Time,${run.startTime || 'N/A'}\n`;
  csv += `End Time,${run.endTime || 'N/A'}\n`;
  
  // Add duration if both start and end time exist
  if (run.startTime && run.endTime) {
    const start = new Date(run.startTime).getTime();
    const end = new Date(run.endTime).getTime();
    const durationMs = end - start;
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    csv += `Duration,${minutes}m ${seconds}s\n`;
  }
  
  // Add error if it exists
  if (run.error) {
    csv += `Error,${run.error.replace(/,/g, ';').replace(/\n/g, ' ')}\n`;
  }
  
  // Add configuration parameters
  csv += '\nConfiguration Parameters\n';
  Object.entries(run.config.parameters).forEach(([key, value]) => {
    csv += `${key},${value}\n`;
  });
  
  // Add input data if it exists
  if (run.config.inputData && Object.keys(run.config.inputData).length > 0) {
    csv += '\nInput Data\n';
    
    // Handle trade IDs
    if (run.config.inputData.tradeIds && run.config.inputData.tradeIds.length > 0) {
      csv += `Trade IDs,${run.config.inputData.tradeIds.join(';')}\n`;
    }
    
    // Handle document IDs
    if (run.config.inputData.documentIds && run.config.inputData.documentIds.length > 0) {
      csv += `Document IDs,${run.config.inputData.documentIds.join(';')}\n`;
    }
    
    // Handle date range
    if (run.config.inputData.dateRange) {
      csv += `Date Range,${run.config.inputData.dateRange.startDate} to ${run.config.inputData.dateRange.endDate}\n`;
    }
    
    // Handle other input data
    Object.entries(run.config.inputData)
      .filter(([key]) => !['tradeIds', 'documentIds', 'dateRange'].includes(key))
      .forEach(([key, value]) => {
        const valueStr = typeof value === 'object' ? JSON.stringify(value).replace(/,/g, ';') : String(value);
        csv += `${key},${valueStr}\n`;
      });
  }
  
  // Add results if they exist
  if (run.results) {
    csv += '\nResults\n';
    csv += `Summary,${run.results.summary.replace(/,/g, ';').replace(/\n/g, ' ')}\n`;
    
    // Add output data
    if (run.results.outputData && Object.keys(run.results.outputData).length > 0) {
      csv += '\nOutput Data\n';
      Object.entries(run.results.outputData).forEach(([key, value]) => {
        const valueStr = typeof value === 'object' ? JSON.stringify(value).replace(/,/g, ';') : String(value);
        csv += `${key},${valueStr}\n`;
      });
    }
    
    // Add generated reports
    if (run.results.generatedReports && run.results.generatedReports.length > 0) {
      csv += '\nGenerated Reports\n';
      csv += 'Name,Type,URL\n';
      run.results.generatedReports.forEach(report => {
        csv += `${report.name},${report.type},${report.url}\n`;
      });
    }
    
    // Add action items
    if (run.results.actionItems && run.results.actionItems.length > 0) {
      csv += '\nAction Items\n';
      csv += 'Description,Type,Status\n';
      run.results.actionItems.forEach(item => {
        csv += `${item.description.replace(/,/g, ';')},${item.type},${item.status}\n`;
      });
    }
  }
  
  // Add metrics if they exist
  if (run.metrics) {
    csv += '\nMetrics\n';
    
    // Add resource usage
    if (run.metrics.resourceUsage) {
      if (run.metrics.resourceUsage.cpu !== undefined) {
        csv += `CPU Usage,${(run.metrics.resourceUsage.cpu * 100).toFixed(1)}%\n`;
      }
      if (run.metrics.resourceUsage.memory !== undefined) {
        csv += `Memory Usage,${run.metrics.resourceUsage.memory} MB\n`;
      }
    }
    
    // Add other metrics
    Object.entries(run.metrics)
      .filter(([key]) => key !== 'resourceUsage')
      .forEach(([key, value]) => {
        const valueStr = typeof value === 'object' ? JSON.stringify(value).replace(/,/g, ';') : String(value);
        csv += `${key},${valueStr}\n`;
      });
  }
  
  return csv;
};

/**
 * Converts multiple agent runs to CSV format for comparison
 */
export const convertRunsToComparisonCSV = (runs: AgentRun[]): string => {
  if (runs.length === 0) return '';
  
  // Start with the header row
  let csv = 'Property';
  runs.forEach((_, index) => {
    csv += `,Run ${index + 1}`;
  });
  csv += '\n';
  
  // Add basic run info
  csv += 'ID';
  runs.forEach(run => {
    csv += `,${run.id}`;
  });
  csv += '\n';
  
  csv += 'Agent Type';
  runs.forEach(run => {
    csv += `,${run.agentType}`;
  });
  csv += '\n';
  
  csv += 'Status';
  runs.forEach(run => {
    csv += `,${run.status}`;
  });
  csv += '\n';
  
  csv += 'Progress';
  runs.forEach(run => {
    csv += `,${run.progress}%`;
  });
  csv += '\n';
  
  csv += 'Start Time';
  runs.forEach(run => {
    csv += `,${run.startTime || 'N/A'}`;
  });
  csv += '\n';
  
  csv += 'End Time';
  runs.forEach(run => {
    csv += `,${run.endTime || 'N/A'}`;
  });
  csv += '\n';
  
  // Add duration
  csv += 'Duration';
  runs.forEach(run => {
    if (run.startTime && run.endTime) {
      const start = new Date(run.startTime).getTime();
      const end = new Date(run.endTime).getTime();
      const durationMs = end - start;
      const minutes = Math.floor(durationMs / 60000);
      const seconds = Math.floor((durationMs % 60000) / 1000);
      csv += `,${minutes}m ${seconds}s`;
    } else {
      csv += ',N/A';
    }
  });
  csv += '\n';
  
  // Add error if any run has one
  if (runs.some(run => run.error)) {
    csv += 'Error';
    runs.forEach(run => {
      csv += `,${run.error ? run.error.replace(/,/g, ';').replace(/\n/g, ' ') : 'N/A'}`;
    });
    csv += '\n';
  }
  
  // Add configuration parameters
  csv += '\nConfiguration Parameters\n';
  
  // Get all unique parameter keys
  const paramKeys = new Set<string>();
  runs.forEach(run => {
    Object.keys(run.config.parameters).forEach(key => paramKeys.add(key));
  });
  
  // Add each parameter
  Array.from(paramKeys).forEach(key => {
    csv += key;
    runs.forEach(run => {
      const value = run.config.parameters[key];
      csv += `,${value !== undefined ? value : 'N/A'}`;
    });
    csv += '\n';
  });
  
  // Add results if any run has them
  if (runs.some(run => run.results)) {
    csv += '\nResults\n';
    
    csv += 'Summary';
    runs.forEach(run => {
      csv += `,${run.results ? run.results.summary.replace(/,/g, ';').replace(/\n/g, ' ') : 'N/A'}`;
    });
    csv += '\n';
    
    // Get all unique output data keys
    const outputKeys = new Set<string>();
    runs.forEach(run => {
      if (run.results?.outputData) {
        Object.keys(run.results.outputData).forEach(key => outputKeys.add(key));
      }
    });
    
    // Add output data if any exists
    if (outputKeys.size > 0) {
      csv += '\nOutput Data\n';
      
      Array.from(outputKeys).forEach(key => {
        csv += key;
        runs.forEach(run => {
          const value = run.results?.outputData?.[key];
          const valueStr = value !== undefined 
            ? (typeof value === 'object' ? JSON.stringify(value).replace(/,/g, ';') : String(value))
            : 'N/A';
          csv += `,${valueStr}`;
        });
        csv += '\n';
      });
    }
  }
  
  // Add metrics if any run has them
  if (runs.some(run => run.metrics)) {
    csv += '\nMetrics\n';
    
    // Add CPU usage
    csv += 'CPU Usage';
    runs.forEach(run => {
      const cpuUsage = run.metrics?.resourceUsage?.cpu;
      csv += `,${cpuUsage !== undefined ? `${(cpuUsage * 100).toFixed(1)}%` : 'N/A'}`;
    });
    csv += '\n';
    
    // Add memory usage
    csv += 'Memory Usage';
    runs.forEach(run => {
      const memoryUsage = run.metrics?.resourceUsage?.memory;
      csv += `,${memoryUsage !== undefined ? `${memoryUsage} MB` : 'N/A'}`;
    });
    csv += '\n';
    
    // Get all unique metric keys
    const metricKeys = new Set<string>();
    runs.forEach(run => {
      if (run.metrics) {
        Object.keys(run.metrics)
          .filter(key => key !== 'resourceUsage')
          .forEach(key => metricKeys.add(key));
      }
    });
    
    // Add other metrics
    Array.from(metricKeys).forEach(key => {
      csv += key;
      runs.forEach(run => {
        const value = run.metrics?.[key];
        const valueStr = value !== undefined 
          ? (typeof value === 'object' ? JSON.stringify(value).replace(/,/g, ';') : String(value))
          : 'N/A';
        csv += `,${valueStr}`;
      });
      csv += '\n';
    });
  }
  
  return csv;
};

/**
 * Downloads data as a file
 */
export const downloadFile = (data: string, filename: string, type: string): void => {
  const blob = new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

/**
 * Generates a shareable link for a run
 */
export const generateShareableLink = (runId: string): string => {
  // In a real implementation, this might call an API to generate a short link
  // For now, we'll just create a link to the current page with the run ID as a query parameter
  const baseUrl = window.location.origin + window.location.pathname;
  const url = new URL(baseUrl);
  url.searchParams.set('runId', runId);
  return url.toString();
};

/**
 * Copies text to clipboard
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
};