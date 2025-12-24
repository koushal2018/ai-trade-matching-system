import { useState } from 'react'
import {
  ContentLayout,
  Header,
  Table,
  Link,
  Badge,
  StatusIndicator,
  Popover,
  Box,
  SpaceBetween,
  Button,
  Pagination,
  PropertyFilter,
  type TableProps,
  type PropertyFilterProps,
} from '@cloudscape-design/components'
import { useCollection } from '@cloudscape-design/collection-hooks'
import { useQuery } from '@tanstack/react-query'
import { auditService } from '../services/auditService'
import type { AuditRecord, AuditActionType, AgentStatusType } from '../types'

const FILTERING_PROPERTIES: PropertyFilterProps.FilteringProperty[] = [
  {
    key: 'actionType',
    propertyLabel: 'Action',
    groupValuesLabel: 'Action values',
    operators: ['=', '!='],
  },
  {
    key: 'outcome',
    propertyLabel: 'Status',
    groupValuesLabel: 'Status values',
    operators: ['=', '!='],
  },
  {
    key: 'user',
    propertyLabel: 'User',
    groupValuesLabel: 'User values',
    operators: ['=', '!=', ':', '!:'],
  },
  {
    key: 'sessionId',
    propertyLabel: 'Session ID',
    groupValuesLabel: 'Session ID values',
    operators: ['=', '!=', ':', '!:'],
  },
]

const getActionBadgeColor = (action: AuditActionType): 'blue' | 'green' | 'red' | 'grey' => {
  switch (action) {
    case 'Upload':
      return 'blue'
    case 'Invoke':
      return 'blue'
    case 'Match Complete':
    case 'TRADE_MATCHED':
      return 'green'
    case 'Exception':
    case 'EXCEPTION_RAISED':
      return 'red'
    case 'Feedback':
    case 'HITL_DECISION':
      return 'grey'
    default:
      return 'grey'
  }
}

const getStatusType = (outcome: string): AgentStatusType => {
  switch (outcome) {
    case 'SUCCESS':
      return 'success'
    case 'FAILURE':
      return 'error'
    case 'PENDING':
      return 'pending'
    default:
      return 'info'
  }
}

export default function AuditTrailPage() {
  const [currentPageIndex, setCurrentPageIndex] = useState(1)
  const [pageSize] = useState(25)

  const { data, isLoading } = useQuery({
    queryKey: ['auditRecords', currentPageIndex, pageSize],
    queryFn: () =>
      auditService.getAuditRecords({
        page: currentPageIndex - 1,
        pageSize,
      }),
  })

  const columnDefinitions: TableProps.ColumnDefinition<AuditRecord>[] = [
    {
      id: 'timestamp',
      header: 'Timestamp',
      cell: (item) => new Date(item.timestamp).toLocaleString(),
      sortingField: 'timestamp',
      isRowHeader: true,
    },
    {
      id: 'sessionId',
      header: 'Session ID',
      cell: (item) => (
        <Link href={`/upload?sessionId=${item.sessionId}`} external={false}>
          {item.sessionId.substring(0, 8)}...
        </Link>
      ),
    },
    {
      id: 'action',
      header: 'Action',
      cell: (item) => (
        <Badge color={getActionBadgeColor(item.actionType)}>
          {item.actionType}
        </Badge>
      ),
    },
    {
      id: 'user',
      header: 'User',
      cell: (item) => item.user || item.agentName || '—',
    },
    {
      id: 'status',
      header: 'Status',
      cell: (item) => (
        <StatusIndicator type={getStatusType(item.outcome)}>
          {item.outcome}
        </StatusIndicator>
      ),
    },
    {
      id: 'details',
      header: 'Details',
      cell: (item) => (
        <Popover
          dismissButton={false}
          position="right"
          size="large"
          triggerType="custom"
          content={
            <SpaceBetween size="s">
              <Box variant="h4">Audit Entry Details</Box>
              
              {/* Basic Information */}
              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">Audit ID</Box>
                <Box variant="code">{item.auditId}</Box>
              </SpaceBetween>
              
              {item.tradeId && (
                <SpaceBetween size="xs">
                  <Box variant="awsui-key-label">Trade ID</Box>
                  <Box>{item.tradeId}</Box>
                </SpaceBetween>
              )}
              
              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">Immutable Hash</Box>
                <Box variant="code" fontSize="body-s">
                  {item.immutableHash}
                </Box>
              </SpaceBetween>
              
              {/* Agent Processing Steps */}
              {item.agentSteps && item.agentSteps.length > 0 && (
                <>
                  <Box variant="h5" margin={{ top: 's' }}>
                    Agent Processing Steps
                  </Box>
                  <SpaceBetween size="xs">
                    {item.agentSteps.map((step, idx) => (
                      <SpaceBetween key={idx} direction="horizontal" size="xs">
                        <StatusIndicator type={step.status}>
                          Step {idx + 1}
                        </StatusIndicator>
                        {step.activity && (
                          <Box variant="small" color="text-body-secondary">
                            {step.activity}
                          </Box>
                        )}
                      </SpaceBetween>
                    ))}
                  </SpaceBetween>
                </>
              )}
              
              {/* Match Results Summary */}
              {item.matchResult && (
                <>
                  <Box variant="h5" margin={{ top: 's' }}>
                    Match Results Summary
                  </Box>
                  <SpaceBetween size="xs">
                    <SpaceBetween direction="horizontal" size="xs">
                      <Box variant="awsui-key-label">Match Status:</Box>
                      <Badge
                        color={
                          item.matchResult.matchStatus === 'MATCHED'
                            ? 'green'
                            : item.matchResult.matchStatus === 'PARTIAL_MATCH'
                            ? 'blue'
                            : 'red'
                        }
                      >
                        {item.matchResult.matchStatus}
                      </Badge>
                    </SpaceBetween>
                    <SpaceBetween direction="horizontal" size="xs">
                      <Box variant="awsui-key-label">Confidence:</Box>
                      <Box>{item.matchResult.confidenceScore}%</Box>
                    </SpaceBetween>
                  </SpaceBetween>
                </>
              )}
              
              {/* Exception Details */}
              {item.exceptions && item.exceptions.length > 0 && (
                <>
                  <Box variant="h5" margin={{ top: 's' }}>
                    Exception Details
                  </Box>
                  <SpaceBetween size="xs">
                    {item.exceptions.map((exception) => (
                      <SpaceBetween key={exception.id} size="xxs">
                        <StatusIndicator type={exception.severity}>
                          {exception.agentName}
                        </StatusIndicator>
                        <Box variant="small">{exception.message}</Box>
                      </SpaceBetween>
                    ))}
                  </SpaceBetween>
                </>
              )}
              
              {/* Additional Details */}
              {item.details && Object.keys(item.details).length > 0 && (
                <>
                  <Box variant="h5" margin={{ top: 's' }}>
                    Additional Details
                  </Box>
                  <Box variant="code" fontSize="body-s">
                    {JSON.stringify(item.details, null, 2)}
                  </Box>
                </>
              )}
            </SpaceBetween>
          }
        >
          <Button variant="inline-icon" iconName="status-info" ariaLabel="View audit entry details" />
        </Popover>
      ),
    },
  ]

  const { items, collectionProps, propertyFilterProps } = useCollection(
    data?.records || [],
    {
      propertyFiltering: {
        filteringProperties: FILTERING_PROPERTIES,
        empty: (
          <Box textAlign="center" color="inherit">
            <b>No audit entries</b>
            <Box variant="p" color="inherit">
              No audit entries match the current filter.
            </Box>
          </Box>
        ),
        noMatch: (
          <Box textAlign="center" color="inherit">
            <b>No matches</b>
            <Box variant="p" color="inherit">
              We can't find a match for your search.
            </Box>
          </Box>
        ),
      },
      sorting: {},
    }
  )

  const handleExportCSV = () => {
    // Convert current filtered items to CSV
    const headers = ['Timestamp', 'Session ID', 'Action', 'User', 'Status', 'Audit ID']
    const csvRows = [
      headers.join(','),
      ...items.map((item) =>
        [
          new Date(item.timestamp).toISOString(),
          item.sessionId,
          item.actionType,
          item.user || item.agentName || '',
          item.outcome,
          item.auditId,
        ]
          .map((field) => `"${field}"`)
          .join(',')
      ),
    ]
    
    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit_trail_${new Date().toISOString()}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="View and filter audit trail of all trade matching operations and agent activity"
          actions={
            <Button iconName="download" onClick={handleExportCSV} ariaLabel="Export audit trail to CSV">
              Export CSV
            </Button>
          }
        >
          Audit Trail
        </Header>
      }
    >
      <Table
        {...collectionProps}
        columnDefinitions={columnDefinitions}
        items={items}
        loading={isLoading}
        loadingText="Loading audit entries..."
        empty={
          <Box textAlign="center" color="inherit">
            <b>No audit entries</b>
            <Box variant="p" color="inherit">
              No audit entries to display.
            </Box>
          </Box>
        }
        filter={
          <PropertyFilter
            {...propertyFilterProps}
            i18nStrings={{
              filteringAriaLabel: 'Filter audit entries',
              dismissAriaLabel: 'Dismiss',
              filteringPlaceholder: 'Filter audit entries by action, status, user, or session ID',
              groupValuesText: 'Values',
              groupPropertiesText: 'Properties',
              operatorsText: 'Operators',
              operationAndText: 'and',
              operationOrText: 'or',
              operatorLessText: 'Less than',
              operatorLessOrEqualText: 'Less than or equal',
              operatorGreaterText: 'Greater than',
              operatorGreaterOrEqualText: 'Greater than or equal',
              operatorContainsText: 'Contains',
              operatorDoesNotContainText: 'Does not contain',
              operatorEqualsText: 'Equals',
              operatorDoesNotEqualText: 'Does not equal',
              editTokenHeader: 'Edit filter',
              propertyText: 'Property',
              operatorText: 'Operator',
              valueText: 'Value',
              cancelActionText: 'Cancel',
              applyActionText: 'Apply',
              allPropertiesLabel: 'All properties',
              tokenLimitShowMore: 'Show more',
              tokenLimitShowFewer: 'Show fewer',
              clearFiltersText: 'Clear filters',
              removeTokenButtonAriaLabel: () => 'Remove token',
              enteredTextLabel: (text) => `Use: "${text}"`,
            }}
            countText={`${items.length} ${items.length === 1 ? 'match' : 'matches'}`}
            expandToViewport
          />
        }
        pagination={
          <Pagination
            currentPageIndex={currentPageIndex}
            onChange={({ detail }) => setCurrentPageIndex(detail.currentPageIndex)}
            pagesCount={Math.ceil((data?.total || 0) / pageSize)}
            ariaLabels={{
              nextPageLabel: 'Next page',
              previousPageLabel: 'Previous page',
              pageLabel: (pageNumber) => `Page ${pageNumber} of all pages`,
            }}
          />
        }
        header={
          <Header
            counter={data?.total ? `(${data.total})` : '(0)'}
            description="Complete history of trade matching operations"
          >
            Audit Entries
          </Header>
        }
      />
    </ContentLayout>
  )
}
