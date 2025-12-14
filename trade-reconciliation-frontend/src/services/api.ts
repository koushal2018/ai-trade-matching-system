import { get, post, put } from 'aws-amplify/api';

// Define API endpoints
const API_NAME = 'tradeApi';

// Dashboard
export const getDashboardData = async () => {
  try {
    return await get({
      apiName: API_NAME,
      path: '/dashboard'
    });
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

// Trades
export const getTrades = async (filters: any = {}) => {
  try {
    return await get({
      apiName: API_NAME,
      path: '/trades',
      options: { queryParams: filters }
    });
  } catch (error) {
    console.error('Error fetching trades:', error);
    throw error;
  }
};

export const getTrade = async (tradeId: string) => {
  try {
    return await get({
      apiName: API_NAME,
      path: `/trades/${tradeId}`
    });
  } catch (error) {
    console.error(`Error fetching trade ${tradeId}:`, error);
    throw error;
  }
};

// Matches
export const getMatches = async (filters: any = {}) => {
  try {
    return await get({
      apiName: API_NAME,
      path: '/matches',
      options: { queryParams: filters }
    });
  } catch (error) {
    console.error('Error fetching matches:', error);
    throw error;
  }
};

export const getMatch = async (matchId: string) => {
  try {
    return await get({
      apiName: API_NAME,
      path: `/matches/${matchId}`
    });
  } catch (error) {
    console.error(`Error fetching match ${matchId}:`, error);
    throw error;
  }
};

export const updateMatchStatus = async (matchId: string, status: string) => {
  try {
    return await put({
      apiName: API_NAME,
      path: `/matches/${matchId}/status`,
      options: {
        body: { status }
      }
    });
  } catch (error) {
    console.error(`Error updating match ${matchId} status:`, error);
    throw error;
  }
};

// Reconciliation
export const getReconciliationDetails = async (matchId: string) => {
  try {
    return await get({
      apiName: API_NAME,
      path: `/reconciliation/${matchId}`
    });
  } catch (error) {
    console.error(`Error fetching reconciliation details for match ${matchId}:`, error);
    throw error;
  }
};

// Reports
export const getReports = async (filters: any = {}) => {
  try {
    return await get({
      apiName: API_NAME,
      path: '/reports',
      options: { queryParams: filters }
    });
  } catch (error) {
    console.error('Error fetching reports:', error);
    throw error;
  }
};

export const getReport = async (reportId: string) => {
  try {
    return await get({
      apiName: API_NAME,
      path: `/reports/${reportId}`
    });
  } catch (error) {
    console.error(`Error fetching report ${reportId}:`, error);
    throw error;
  }
};

export const generateReport = async (params: any) => {
  try {
    return await post({
      apiName: API_NAME,
      path: '/reports',
      options: {
        body: params
      }
    });
  } catch (error) {
    console.error('Error generating report:', error);
    throw error;
  }
};

// Admin Settings
export const getSettings = async () => {
  try {
    return await get({
      apiName: API_NAME,
      path: '/settings'
    });
  } catch (error) {
    console.error('Error fetching settings:', error);
    throw error;
  }
};

export const updateSettings = async (settings: any) => {
  try {
    return await put({
      apiName: API_NAME,
      path: '/settings',
      options: {
        body: settings
      }
    });
  } catch (error) {
    console.error('Error updating settings:', error);
    throw error;
  }
};