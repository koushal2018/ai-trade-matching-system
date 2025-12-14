/**
 * SystemHealthService provides utilities for working with system health data
 */

import { SystemHealth } from '../../types/agent';

export class SystemHealthService {
  /**
   * Gets the status color for a health status
   */
  public static getStatusColor(status: 'healthy' | 'degraded' | 'unhealthy'): string {
    switch (status) {
      case 'healthy':
        return 'green';
      case 'degraded':
        return 'yellow';
      case 'unhealthy':
        return 'red';
      default:
        return 'gray';
    }
  }

  /**
   * Gets the CSS class for a health status
   */
  public static getStatusClass(status: 'healthy' | 'degraded' | 'unhealthy'): string {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'unhealthy':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  /**
   * Gets the CSS class for a resource usage level
   */
  public static getResourceUsageClass(usage: number): string {
    if (usage < 50) {
      return 'bg-green-500';
    } else if (usage < 80) {
      return 'bg-yellow-500';
    } else {
      return 'bg-red-500';
    }
  }

  /**
   * Formats uptime in a human-readable format
   */
  public static formatUptime(uptime: number): string {
    const days = Math.floor(uptime / (24 * 60 * 60));
    const hours = Math.floor((uptime % (24 * 60 * 60)) / (60 * 60));
    const minutes = Math.floor((uptime % (60 * 60)) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  /**
   * Checks if the system health is critical
   */
  public static isCritical(health: SystemHealth): boolean {
    return health.status === 'unhealthy' ||
      health.metrics.cpu > 90 ||
      health.metrics.memory > 90 ||
      health.metrics.disk > 90;
  }

  /**
   * Gets a summary of the system health
   */
  public static getSummary(health: SystemHealth): string {
    if (health.status === 'healthy') {
      return 'All systems operational';
    } else if (health.status === 'degraded') {
      return 'Some systems experiencing issues';
    } else {
      return 'Critical system issues detected';
    }
  }

  /**
   * Gets the number of agents with issues
   */
  public static getAgentsWithIssues(health: SystemHealth): number {
    return Object.values(health.agents).filter(agent => agent.status !== 'healthy').length;
  }
}