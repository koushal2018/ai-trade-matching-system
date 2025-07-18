import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { get } from 'aws-amplify/api';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Doughnut, Line } from 'react-chartjs-2';
import axios from 'axios';

// Register ChartJS components
ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const Dashboard: React.FC = () => {
  const [summaryData, setSummaryData] = useState({
    matched: 0,
    partiallyMatched: 0,
    unmatched: 0,
    total: 0
  });
  const [tradeData, setTradeData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTradeData = async () => {
      try {
        // Fetch real data from our API Gateway endpoint
        const response = await axios.get('https://mdj9ch24qg.execute-api.us-east-1.amazonaws.com/dev/trades');
        
        // Process the data
        const trades = response.data.trades || [];
        setTradeData(trades);
        
        // Calculate summary data
        const matched = trades.filter((trade: any) => trade.matched_status === 'MATCHED').length;
        const partiallyMatched = trades.filter((trade: any) => trade.matched_status === 'PARTIALLY_MATCHED').length;
        const unmatched = trades.filter((trade: any) => 
          trade.matched_status === 'PENDING' || 
          trade.matched_status === 'UNMATCHED' || 
          trade.matched_status === 'Unreconciled'
        ).length;
        
        setSummaryData({
          matched,
          partiallyMatched,
          unmatched,
          total: trades.length
        });
        
        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching trade data:', err);
        setError(err.message || 'Failed to load trade data');
        setLoading(false);
      }
    };

    fetchTradeData();
  }, []);

  // Prepare chart data
  const statusChartData = {
    labels: ['Matched', 'Partially Matched', 'Unmatched'],
    datasets: [
      {
        data: [summaryData.matched, summaryData.partiallyMatched, summaryData.unmatched],
        backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
        borderColor: ['#10B981', '#F59E0B', '#EF4444'],
        borderWidth: 1,
      },
    ],
  };

  // Process trade data for time series chart
  const processTimeSeriesData = () => {
    // Group trades by date
    const tradesByDate = tradeData.reduce((acc: {[key: string]: number}, trade: any) => {
      // Extract date from trade_date or processing_timestamp
      const dateStr = trade.trade_date || 
                     (trade.processing_timestamp ? trade.processing_timestamp.split('T')[0] : '');
      
      if (dateStr) {
        // Format date for display (e.g., "Jul 10")
        const date = new Date(dateStr);
        const formattedDate = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        acc[formattedDate] = (acc[formattedDate] || 0) + 1;
      }
      return acc;
    }, {});
    
    // Sort dates
    const sortedDates = Object.keys(tradesByDate).sort((a, b) => {
      return new Date(a).getTime() - new Date(b).getTime();
    });
    
    // Limit to last 10 dates if there are more
    const displayDates = sortedDates.slice(-10);
    const displayCounts = displayDates.map(date => tradesByDate[date]);
    
    return {
      labels: displayDates,
      datasets: [
        {
          label: 'Trades Processed',
          data: displayCounts,
          borderColor: '#0EA5E9',
          backgroundColor: 'rgba(14, 165, 233, 0.2)',
          tension: 0.4,
          fill: true,
        },
      ],
    };
  };
  
  // Line chart data for trades processed over time
  const timeSeriesData = tradeData.length > 0 ? processTimeSeriesData() : {
    labels: [],
    datasets: [
      {
        label: 'Trades Processed',
        data: [],
        borderColor: '#0EA5E9',
        backgroundColor: 'rgba(14, 165, 233, 0.2)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-primary-100 rounded-md p-3">
                <svg className="h-6 w-6 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">Total Trades</dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">{summaryData.total}</div>
                </dd>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                <svg className="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">Matched Trades</dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">{summaryData.matched}</div>
                </dd>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-yellow-100 rounded-md p-3">
                <svg className="h-6 w-6 text-yellow-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">Partially Matched</dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">{summaryData.partiallyMatched}</div>
                </dd>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-red-100 rounded-md p-3">
                <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dt className="text-sm font-medium text-gray-500 truncate">Unmatched Trades</dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">{summaryData.unmatched}</div>
                </dd>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Status Distribution</h3>
            <div className="h-64 flex justify-center">
              <Doughnut 
                data={statusChartData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    },
                  },
                }} 
              />
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Trades Processed Over Time</h3>
            <div className="h-64">
              <Line 
                data={timeSeriesData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false,
                    },
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                    },
                  },
                }} 
              />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="mt-8 bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Quick Links</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Link
              to="/upload"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
            >
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Upload Trade PDFs</p>
              </div>
            </Link>

            <Link
              to="/reports"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
            >
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">View Reports</p>
              </div>
            </Link>

            <Link
              to="/trades"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
            >
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Trade Explorer</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;