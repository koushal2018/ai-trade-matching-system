/**
 * Status mapping utilities for the Trade Matching System
 * Maps internal status values to user-friendly display strings
 */

/**
 * Maps overallStatus values from DynamoDB to user-friendly display strings
 * 
 * @param status - The overallStatus value from Processing_Status table
 * @returns User-friendly status string
 * 
 * Mappings:
 * - pending → Pending
 * - initializing → Initializing
 * - processing → In Progress
 * - completed → Completed
 * - failed → Failed
 * - (unmapped) → Unknown
 * 
 * Requirements: 8.4, 8.5, 8.6, 8.7, 8.8, 8.13
 */
export function mapOverallStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'pending': 'Pending',
    'initializing': 'Initializing',
    'processing': 'In Progress',
    'completed': 'Completed',
    'failed': 'Failed'
  }
  
  return statusMap[status] || 'Unknown'
}
