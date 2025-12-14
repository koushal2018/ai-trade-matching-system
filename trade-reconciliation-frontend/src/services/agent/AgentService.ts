/**
 * AgentService provides methods for interacting with the agent API
 */

import { BaseApiService, ApiResponse } from '../api/BaseApiService';
import { ErrorHandler, EnhancedError } from '../api/ErrorHandler';
import { WebSocketService } from '../api/WebSocketService';
import { API_BASE_URL, API_ENDPOINTS, WS_ENDPOINTS } from '../../config/api';
import {
  AgentRun,
  AgentRunConfig,
  AgentThinkingStep,
  RunHistoryFilters,
  SavedConfiguration,
  AgentSettings,
  SystemHealth,
} from '../../types/agent';

export class AgentService extends BaseApiService {
  private wsThinking: Map<string, WebSocketService> = new Map();
  private wsStatus: WebSocketService | null = null;

  constructor() {
    super(API_BASE_URL);
  }

  /**
   * Triggers a new agent run
   */
  public async triggerRun(config: AgentRunConfig): Promise<string> {
    try {
      const response = await this.post<{ runId: string }>(API_ENDPOINTS.AGENT.RUNS, config);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.runId;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to trigger agent run',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Cancels an ongoing agent run
   */
  public async cancelRun(runId: string): Promise<boolean> {
    try {
      const response = await this.post<{ success: boolean }>(API_ENDPOINTS.AGENT.CANCEL_RUN(runId));
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.success;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to cancel agent run',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Gets details of a specific agent run
   */
  public async getRun(runId: string): Promise<AgentRun> {
    try {
      const response = await this.get<AgentRun>(API_ENDPOINTS.AGENT.RUN_DETAIL(runId));
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get agent run details',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Gets all active agent runs
   */
  public async getActiveRuns(): Promise<AgentRun[]> {
    try {
      const response = await this.get<AgentRun[]>(`${API_ENDPOINTS.AGENT.RUNS}?status=active`);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get active agent runs',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Gets historical agent runs with optional filtering
   */
  public async getRunHistory(filters?: RunHistoryFilters): Promise<ApiResponse<{ runs: AgentRun[], total: number }>> {
    try {
      // Build query string from filters
      const queryParams = new URLSearchParams();
      
      if (filters) {
        if (filters.agentType) queryParams.append('agentType', filters.agentType);
        if (filters.status) queryParams.append('status', filters.status);
        if (filters.startDate) queryParams.append('startDate', filters.startDate);
        if (filters.endDate) queryParams.append('endDate', filters.endDate);
        if (filters.page !== undefined) queryParams.append('page', filters.page.toString());
        if (filters.pageSize !== undefined) queryParams.append('pageSize', filters.pageSize.toString());
        if (filters.sortBy) queryParams.append('sortBy', filters.sortBy);
        if (filters.sortDirection) queryParams.append('sortDirection', filters.sortDirection);
      }
      
      const queryString = queryParams.toString();
      const endpoint = queryString ? `${API_ENDPOINTS.AGENT.RUNS}?${queryString}` : API_ENDPOINTS.AGENT.RUNS;
      
      return await this.get<{ runs: AgentRun[], total: number }>(endpoint);
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get agent run history',
      };
      
      ErrorHandler.logError(apiError);
      return { error: apiError };
    }
  }

  /**
   * Gets the thinking process for a specific agent run
   */
  public async getThinkingProcess(runId: string): Promise<AgentThinkingStep[]> {
    try {
      const response = await this.get<AgentThinkingStep[]>(API_ENDPOINTS.AGENT.THINKING_PROCESS(runId));
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get agent thinking process',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Subscribes to real-time updates of an agent's thinking process
   */
  public subscribeToThinkingProcess(
    runId: string,
    callback: (step: AgentThinkingStep) => void
  ): Promise<() => void> {
    return new Promise((resolve, reject) => {
      try {
        // Check if we already have a WebSocket for this run
        if (this.wsThinking.has(runId)) {
          const ws = this.wsThinking.get(runId)!;
          
          // If it's already connected, just add the callback
          if (ws.isConnected()) {
            const unsubscribe = ws.on('thinking_step', callback);
            resolve(unsubscribe);
            return;
          }
          
          // Otherwise, disconnect and create a new one
          ws.disconnect();
          this.wsThinking.delete(runId);
        }
        
        // Create a new WebSocket
        const wsUrl = `${API_BASE_URL.replace('http', 'ws')}${WS_ENDPOINTS.AGENT_THINKING(runId)}`;
        const ws = new WebSocketService(wsUrl, {
          reconnectAttempts: 5,
          reconnectDelay: 1000,
        });
        
        this.wsThinking.set(runId, ws);
        
        // Connect to the WebSocket
        ws.connect()
          .then(() => {
            const unsubscribe = ws.on('thinking_step', callback);
            resolve(unsubscribe);
          })
          .catch(error => {
            reject(error);
          });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Subscribes to real-time updates of agent run statuses
   */
  public subscribeToRunStatus(
    callback: (runs: AgentRun[]) => void
  ): Promise<() => void> {
    return new Promise((resolve, reject) => {
      try {
        // Check if we already have a WebSocket for run status
        if (this.wsStatus && this.wsStatus.isConnected()) {
          const unsubscribe = this.wsStatus.on('run_status', callback);
          resolve(unsubscribe);
          return;
        }
        
        // Create a new WebSocket
        const wsUrl = `${API_BASE_URL.replace('http', 'ws')}${WS_ENDPOINTS.AGENT_STATUS}`;
        this.wsStatus = new WebSocketService(wsUrl, {
          reconnectAttempts: 5,
          reconnectDelay: 1000,
        });
        
        // Connect to the WebSocket
        this.wsStatus.connect()
          .then(() => {
            const unsubscribe = this.wsStatus!.on('run_status', callback);
            resolve(unsubscribe);
          })
          .catch(error => {
            reject(error);
          });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Gets all saved configurations
   */
  public async getSavedConfigurations(): Promise<SavedConfiguration[]> {
    try {
      const response = await this.get<SavedConfiguration[]>(API_ENDPOINTS.AGENT.CONFIGURATIONS);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get saved configurations',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Gets a specific saved configuration
   */
  public async getSavedConfiguration(configId: string): Promise<SavedConfiguration> {
    try {
      const response = await this.get<SavedConfiguration>(API_ENDPOINTS.AGENT.CONFIGURATION_DETAIL(configId));
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get saved configuration',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Saves a configuration
   */
  public async saveConfiguration(config: Omit<SavedConfiguration, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
    try {
      const response = await this.post<{ configId: string }>(API_ENDPOINTS.AGENT.CONFIGURATIONS, config);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.configId;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to save configuration',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Updates a saved configuration
   */
  public async updateConfiguration(configId: string, config: Omit<SavedConfiguration, 'id' | 'createdAt' | 'updatedAt'>): Promise<boolean> {
    try {
      const response = await this.put<{ success: boolean }>(API_ENDPOINTS.AGENT.CONFIGURATION_DETAIL(configId), config);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.success;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to update configuration',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Deletes a saved configuration
   */
  public async deleteConfiguration(configId: string): Promise<boolean> {
    try {
      const response = await this.delete<{ success: boolean }>(API_ENDPOINTS.AGENT.CONFIGURATION_DETAIL(configId));
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.success;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to delete configuration',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Gets agent settings
   */
  public async getSettings(): Promise<AgentSettings> {
    try {
      const response = await this.get<AgentSettings>(API_ENDPOINTS.AGENT.SETTINGS);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get agent settings',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Updates agent settings
   */
  public async updateSettings(settings: AgentSettings): Promise<boolean> {
    try {
      const response = await this.put<{ success: boolean }>(API_ENDPOINTS.AGENT.SETTINGS, settings);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.success;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to update agent settings',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Gets system health information
   */
  public async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await this.get<SystemHealth>(API_ENDPOINTS.AGENT.SYSTEM_HEALTH);
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to get system health',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }
  
  /**
   * Exports a run in the specified format
   */
  public async exportRun(runId: string, format: 'json' | 'csv' | 'pdf'): Promise<Blob> {
    try {
      // Use fetch directly to get the blob response
      const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.AGENT.EXPORT_RUN(runId, format)}`, {
        method: 'GET',
        headers: {
          'Accept': format === 'json' ? 'application/json' : 
                   format === 'csv' ? 'text/csv' : 
                   'application/pdf',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to export run: ${response.statusText}`);
      }
      
      return await response.blob();
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || `Failed to export run as ${format}`,
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }
  
  /**
   * Generates a shareable link for a run
   */
  public async generateShareableLink(runId: string): Promise<string> {
    try {
      const response = await this.post<{ url: string }>(API_ENDPOINTS.AGENT.SHARE_RUN(runId));
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.url;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || 'Failed to generate shareable link',
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }
  
  /**
   * Archives or unarchives a run
   */
  public async archiveRun(runId: string, archive: boolean): Promise<boolean> {
    try {
      const response = await this.post<{ success: boolean }>(
        archive ? API_ENDPOINTS.AGENT.ARCHIVE_RUN(runId) : API_ENDPOINTS.AGENT.UNARCHIVE_RUN(runId)
      );
      
      if (response.error) {
        ErrorHandler.logError(response.error);
        throw new Error(response.error.message);
      }
      
      return response.data!.success;
    } catch (error) {
      const apiError = {
        status: (error as any).status || 0,
        message: (error as Error).message || `Failed to ${archive ? 'archive' : 'unarchive'} run`,
      };
      
      ErrorHandler.logError(apiError);
      throw new Error(apiError.message);
    }
  }

  /**
   * Creates a singleton instance of the AgentService
   */
  private static instance: AgentService;
  
  public static getInstance(): AgentService {
    if (!AgentService.instance) {
      AgentService.instance = new AgentService();
    }
    
    return AgentService.instance;
  }
}