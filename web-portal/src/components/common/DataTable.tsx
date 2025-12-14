import React, { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Checkbox,
  IconButton,
  Box,
  Typography,
  Skeleton,
  TextField,
  InputAdornment,
  Pagination,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Search as SearchIcon,
  GetApp as ExportIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'

export interface Column<T = any> {
  id: keyof T
  label: string
  minWidth?: number
  align?: 'right' | 'left' | 'center'
  sortable?: boolean
  format?: (value: any) => string | React.ReactNode
  filterable?: boolean
  filterType?: 'text' | 'select' | 'date'
  filterOptions?: Array<{ value: string; label: string }>
}

export interface DataTableProps<T = any> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  selectable?: boolean
  searchable?: boolean
  filterable?: boolean
  exportable?: boolean
  pagination?: boolean
  pageSize?: number
  onRowClick?: (row: T) => void
  onEdit?: (row: T) => void
  onDelete?: (row: T) => void
  onExport?: () => void
  emptyMessage?: string
  title?: string
}

type Order = 'asc' | 'desc'

export default function DataTable<T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  selectable = false,
  searchable = true,
  filterable = true,
  exportable = false,
  pagination = true,
  pageSize = 10,
  onRowClick,
  onEdit,
  onDelete,
  onExport,
  emptyMessage = 'No data available',
  title,
}: DataTableProps<T>) {
  const [order, setOrder] = useState<Order>('asc')
  const [orderBy, setOrderBy] = useState<keyof T>(columns[0]?.id)
  const [selected, setSelected] = useState<readonly string[]>([])
  const [page, setPage] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState<Record<string, string>>({})

  const handleRequestSort = (property: keyof T) => {
    const isAsc = orderBy === property && order === 'asc'
    setOrder(isAsc ? 'desc' : 'asc')
    setOrderBy(property)
  }

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = data.map((_, index) => index.toString())
      setSelected(newSelected)
      return
    }
    setSelected([])
  }

  const handleClick = (_: React.MouseEvent<unknown>, id: string) => {
    if (!selectable) return
    
    const selectedIndex = selected.indexOf(id)
    let newSelected: readonly string[] = []

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id)
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1))
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1))
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      )
    }
    setSelected(newSelected)
  }

  const isSelected = (id: string) => selected.indexOf(id) !== -1

  // Filter and search data
  const filteredData = React.useMemo(() => {
    let filtered = [...data]

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter((row) =>
        columns.some((column) => {
          const value = row[column.id]
          return value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
        })
      )
    }

    // Apply filters
    Object.entries(filters).forEach(([columnId, filterValue]) => {
      if (filterValue) {
        filtered = filtered.filter((row) => {
          const value = row[columnId]
          return value?.toString().toLowerCase().includes(filterValue.toLowerCase())
        })
      }
    })

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[orderBy]
      const bValue = b[orderBy]
      
      if (aValue < bValue) {
        return order === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return order === 'asc' ? 1 : -1
      }
      return 0
    })

    return filtered
  }, [data, searchTerm, filters, order, orderBy, columns])

  // Paginate data
  const paginatedData = React.useMemo(() => {
    if (!pagination) return filteredData
    const startIndex = page * pageSize
    return filteredData.slice(startIndex, startIndex + pageSize)
  }, [filteredData, page, pageSize, pagination])

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage - 1) // MUI Pagination is 1-indexed
  }

  const handleFilterChange = (columnId: string, value: string) => {
    setFilters(prev => ({ ...prev, [columnId]: value }))
    setPage(0) // Reset to first page when filtering
  }

  return (
    <Paper sx={{ 
      width: '100%', 
      overflow: 'hidden',
      background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(65, 77, 92, 0.3)',
    }}>
      {/* Header */}
      {(title || searchable || exportable) && (
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(65, 77, 92, 0.3)' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={searchable || filterable ? 2 : 0}>
            {title && (
              <Typography variant="h6" fontWeight={600} color="text.primary">
                {title}
              </Typography>
            )}
            <Box display="flex" gap={1}>
              {exportable && (
                <IconButton 
                  onClick={onExport}
                  sx={{ 
                    color: 'text.secondary',
                    '&:hover': { 
                      backgroundColor: 'rgba(255, 153, 0, 0.08)',
                      color: 'primary.main'
                    }
                  }}
                >
                  <ExportIcon />
                </IconButton>
              )}
            </Box>
          </Box>

          {/* Search and Filters */}
          {(searchable || filterable) && (
            <Box display="flex" gap={2} flexWrap="wrap">
              {searchable && (
                <TextField
                  size="small"
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon sx={{ color: 'text.secondary' }} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ 
                    minWidth: 250,
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: 'rgba(65, 77, 92, 0.1)',
                      '&:hover': {
                        backgroundColor: 'rgba(65, 77, 92, 0.15)',
                      },
                      '&.Mui-focused': {
                        backgroundColor: 'rgba(65, 77, 92, 0.2)',
                      }
                    }
                  }}
                />
              )}

              {filterable && columns.filter(col => col.filterable).map((column) => (
                <FormControl key={column.id.toString()} size="small" sx={{ minWidth: 120 }}>
                  <InputLabel sx={{ color: 'text.secondary' }}>
                    {column.label}
                  </InputLabel>
                  {column.filterType === 'select' && column.filterOptions ? (
                    <Select
                      value={filters[column.id.toString()] || ''}
                      onChange={(e) => handleFilterChange(column.id.toString(), e.target.value)}
                      label={column.label}
                      sx={{
                        backgroundColor: 'rgba(65, 77, 92, 0.1)',
                        '&:hover': {
                          backgroundColor: 'rgba(65, 77, 92, 0.15)',
                        }
                      }}
                    >
                      <MenuItem value="">All</MenuItem>
                      {column.filterOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  ) : (
                    <TextField
                      size="small"
                      value={filters[column.id.toString()] || ''}
                      onChange={(e) => handleFilterChange(column.id.toString(), e.target.value)}
                      placeholder={`Filter ${column.label}`}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          backgroundColor: 'rgba(65, 77, 92, 0.1)',
                          '&:hover': {
                            backgroundColor: 'rgba(65, 77, 92, 0.15)',
                          }
                        }
                      }}
                    />
                  )}
                </FormControl>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Table */}
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {selectable && (
                <TableCell 
                  padding="checkbox"
                  sx={{ 
                    backgroundColor: 'rgba(35, 42, 49, 0.95)',
                    borderBottom: '1px solid rgba(65, 77, 92, 0.3)'
                  }}
                >
                  <Checkbox
                    color="primary"
                    indeterminate={selected.length > 0 && selected.length < data.length}
                    checked={data.length > 0 && selected.length === data.length}
                    onChange={handleSelectAllClick}
                    sx={{ color: 'text.secondary' }}
                  />
                </TableCell>
              )}
              {columns.map((column) => (
                <TableCell
                  key={column.id.toString()}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                  sx={{ 
                    backgroundColor: 'rgba(35, 42, 49, 0.95)',
                    borderBottom: '1px solid rgba(65, 77, 92, 0.3)',
                    color: 'text.primary',
                    fontWeight: 600
                  }}
                >
                  {column.sortable !== false ? (
                    <TableSortLabel
                      active={orderBy === column.id}
                      direction={orderBy === column.id ? order : 'asc'}
                      onClick={() => handleRequestSort(column.id)}
                      sx={{
                        color: 'text.primary !important',
                        '&.Mui-active': {
                          color: 'primary.main !important',
                        },
                        '& .MuiTableSortLabel-icon': {
                          color: 'primary.main !important',
                        }
                      }}
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
              {(onEdit || onDelete || onRowClick) && (
                <TableCell 
                  align="center"
                  sx={{ 
                    backgroundColor: 'rgba(35, 42, 49, 0.95)',
                    borderBottom: '1px solid rgba(65, 77, 92, 0.3)',
                    color: 'text.primary',
                    fontWeight: 600
                  }}
                >
                  Actions
                </TableCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              // Loading skeleton
              Array.from({ length: pageSize }).map((_, index) => (
                <TableRow key={index}>
                  {selectable && (
                    <TableCell padding="checkbox">
                      <Skeleton variant="rectangular" width={20} height={20} />
                    </TableCell>
                  )}
                  {columns.map((column) => (
                    <TableCell key={column.id.toString()}>
                      <Skeleton variant="text" />
                    </TableCell>
                  ))}
                  {(onEdit || onDelete || onRowClick) && (
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                  )}
                </TableRow>
              ))
            ) : paginatedData.length === 0 ? (
              // Empty state
              <TableRow>
                <TableCell 
                  colSpan={columns.length + (selectable ? 1 : 0) + ((onEdit || onDelete || onRowClick) ? 1 : 0)}
                  sx={{ textAlign: 'center', py: 6 }}
                >
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    {emptyMessage}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {searchTerm || Object.values(filters).some(f => f) 
                      ? 'Try adjusting your search or filters'
                      : 'Data will appear here when available'
                    }
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              // Data rows
              paginatedData.map((row, index) => {
                const isItemSelected = isSelected(index.toString())
                const labelId = `enhanced-table-checkbox-${index}`

                return (
                  <TableRow
                    hover
                    onClick={(event) => {
                      if (selectable) {
                        handleClick(event, index.toString())
                      } else if (onRowClick) {
                        onRowClick(row)
                      }
                    }}
                    role="checkbox"
                    aria-checked={isItemSelected}
                    tabIndex={-1}
                    key={index}
                    selected={isItemSelected}
                    sx={{
                      cursor: (selectable || onRowClick) ? 'pointer' : 'default',
                      '&:hover': {
                        backgroundColor: 'rgba(255, 153, 0, 0.04)',
                      },
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(255, 153, 0, 0.08)',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 153, 0, 0.12)',
                        }
                      }
                    }}
                  >
                    {selectable && (
                      <TableCell padding="checkbox">
                        <Checkbox
                          color="primary"
                          checked={isItemSelected}
                          inputProps={{
                            'aria-labelledby': labelId,
                          }}
                        />
                      </TableCell>
                    )}
                    {columns.map((column) => {
                      const value = row[column.id]
                      return (
                        <TableCell 
                          key={column.id.toString()} 
                          align={column.align}
                          sx={{ color: 'text.primary' }}
                        >
                          {column.format ? column.format(value) : value}
                        </TableCell>
                      )
                    })}
                    {(onEdit || onDelete || onRowClick) && (
                      <TableCell align="center">
                        <Box display="flex" justifyContent="center" gap={0.5}>
                          {onRowClick && (
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                onRowClick(row)
                              }}
                              sx={{
                                color: 'text.secondary',
                                '&:hover': {
                                  backgroundColor: 'rgba(20, 110, 180, 0.08)',
                                  color: 'secondary.main'
                                }
                              }}
                            >
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          )}
                          {onEdit && (
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                onEdit(row)
                              }}
                              sx={{
                                color: 'text.secondary',
                                '&:hover': {
                                  backgroundColor: 'rgba(255, 153, 0, 0.08)',
                                  color: 'primary.main'
                                }
                              }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          )}
                          {onDelete && (
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                onDelete(row)
                              }}
                              sx={{
                                color: 'text.secondary',
                                '&:hover': {
                                  backgroundColor: 'rgba(209, 50, 18, 0.08)',
                                  color: 'error.main'
                                }
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          )}
                        </Box>
                      </TableCell>
                    )}
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {pagination && !loading && filteredData.length > pageSize && (
        <Box 
          display="flex" 
          justifyContent="space-between" 
          alignItems="center" 
          sx={{ 
            p: 2, 
            borderTop: '1px solid rgba(65, 77, 92, 0.3)',
            backgroundColor: 'rgba(35, 42, 49, 0.5)'
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, filteredData.length)} of {filteredData.length} results
          </Typography>
          <Pagination
            count={Math.ceil(filteredData.length / pageSize)}
            page={page + 1}
            onChange={handleChangePage}
            color="primary"
            sx={{
              '& .MuiPaginationItem-root': {
                color: 'text.secondary',
                '&:hover': {
                  backgroundColor: 'rgba(255, 153, 0, 0.08)',
                },
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: '#FFFFFF',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  }
                }
              }
            }}
          />
        </Box>
      )}
    </Paper>
  )
}