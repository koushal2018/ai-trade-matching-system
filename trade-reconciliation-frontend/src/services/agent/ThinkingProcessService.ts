/**
 * ThinkingProcessService provides utilities for working with agent thinking process data
 */

import { AgentThinkingStep, AgentThinkingStepType } from '../../types/agent';

export class ThinkingProcessService {
  /**
   * Organizes thinking steps into a hierarchical structure
   */
  public static organizeHierarchy(steps: AgentThinkingStep[]): AgentThinkingStep[] {
    // Create a map of steps by ID for quick lookup
    const stepsMap = new Map<string, AgentThinkingStep & { children?: AgentThinkingStep[] }>();
    
    // First pass: add all steps to the map
    steps.forEach(step => {
      stepsMap.set(step.id, { ...step, children: [] });
    });
    
    // Second pass: organize steps into a hierarchy
    const rootSteps: AgentThinkingStep[] = [];
    
    steps.forEach(step => {
      const enhancedStep = stepsMap.get(step.id)!;
      
      if (step.parentId && stepsMap.has(step.parentId)) {
        // This step has a parent, add it to the parent's children
        const parent = stepsMap.get(step.parentId)!;
        parent.children!.push(enhancedStep);
      } else {
        // This is a root step
        rootSteps.push(enhancedStep);
      }
    });
    
    return rootSteps;
  }

  /**
   * Filters thinking steps by type
   */
  public static filterByType(steps: AgentThinkingStep[], types: AgentThinkingStepType[]): AgentThinkingStep[] {
    if (!types.length) {
      return steps;
    }
    
    return steps.filter(step => types.includes(step.type));
  }

  /**
   * Searches thinking steps for a query string
   */
  public static search(steps: AgentThinkingStep[], query: string): AgentThinkingStep[] {
    if (!query) {
      return steps;
    }
    
    const lowerQuery = query.toLowerCase();
    
    return steps.filter(step => {
      return step.content.toLowerCase().includes(lowerQuery) ||
        (step.metadata && JSON.stringify(step.metadata).toLowerCase().includes(lowerQuery));
    });
  }

  /**
   * Formats a thinking step for display
   */
  public static formatStepContent(step: AgentThinkingStep): string {
    // Format based on step type
    if (step.type === 'error') {
      // Highlight error messages
      return `ERROR: ${step.content}`;
    }
    
    // You could add markdown formatting, syntax highlighting, etc. here
    return step.content;
  }

  /**
   * Gets the CSS class for a thinking step type
   */
  public static getStepTypeClass(type: AgentThinkingStepType): string {
    switch (type) {
      case 'action':
        return 'bg-blue-100 text-blue-800';
      case 'decision':
        return 'bg-purple-100 text-purple-800';
      case 'observation':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'info':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  /**
   * Gets the icon for a thinking step type
   */
  public static getStepTypeIcon(type: AgentThinkingStepType): string {
    switch (type) {
      case 'action':
        return 'play';
      case 'decision':
        return 'lightbulb';
      case 'observation':
        return 'eye';
      case 'error':
        return 'exclamation-triangle';
      case 'info':
      default:
        return 'info-circle';
    }
  }
}