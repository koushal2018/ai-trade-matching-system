// Trade Reconciliation System - Frontend Configuration
// This file should be included in the Amplify build process

const configureEnvironment = () => {
  // Get environment variables from Amplify build settings
  const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || '';
  const REGION = process.env.REACT_APP_REGION || 'us-east-1';
  const USER_POOL_ID = process.env.REACT_APP_USER_POOL_ID || '';
  const USER_POOL_CLIENT_ID = process.env.REACT_APP_USER_POOL_CLIENT_ID || '';
  const ENVIRONMENT = process.env.REACT_APP_ENVIRONMENT || 'dev';

  // Validate required configuration
  if (!API_ENDPOINT) {
    console.error('API_ENDPOINT is not configured. Frontend will not function correctly.');
  }

  if (!USER_POOL_ID || !USER_POOL_CLIENT_ID) {
    console.warn('Authentication is not fully configured. Some features may not work properly.');
  }

  return {
    // API configuration
    API_CONFIG: {
      API_ENDPOINT: API_ENDPOINT,
      REGION: REGION
    },

    // Authentication configuration (Cognito)
    AUTH_CONFIG: {
      region: REGION,
      userPoolId: USER_POOL_ID,
      userPoolWebClientId: USER_POOL_CLIENT_ID,
      mandatorySignIn: true,
      authenticationFlowType: 'USER_SRP_AUTH'
    },

    // Amplify configuration
    AMPLIFY_CONFIG: {
      Auth: {
        region: REGION,
        userPoolId: USER_POOL_ID,
        userPoolWebClientId: USER_POOL_CLIENT_ID,
        mandatorySignIn: true,
        authenticationFlowType: 'USER_SRP_AUTH'
      },
      API: {
        endpoints: [
          {
            name: 'tradeApi',
            endpoint: API_ENDPOINT,
            region: REGION,
            custom_header: async () => {
              return {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
              };
            }
          }
        ]
      }
    },

    // Feature flags for environment-specific functionality
    FEATURES: {
      enableReports: ENVIRONMENT !== 'dev',
      enableBatchUploads: ENVIRONMENT === 'prod',
      enableAdminPanel: ENVIRONMENT !== 'dev',
      enableNotifications: true,
      maxFileSize: 50 * 1024 * 1024, // 50MB
      supportedFileFormats: ['pdf', 'csv', 'xlsx', 'xls', 'xml']
    },

    // Environment-specific settings
    ENV_SETTINGS: {
      environment: ENVIRONMENT,
      isProduction: ENVIRONMENT === 'prod',
      version: process.env.REACT_APP_VERSION || '1.0.0',
      buildId: process.env.REACT_APP_BUILD_ID || new Date().toISOString()
    }
  };
};

// Export the configuration
const config = configureEnvironment();
export const API_CONFIG = config.API_CONFIG;
export const AUTH_CONFIG = config.AUTH_CONFIG;
export const AMPLIFY_CONFIG = config.AMPLIFY_CONFIG;
export const FEATURES = config.FEATURES;
export const ENV_SETTINGS = config.ENV_SETTINGS;

// For backwards compatibility
export default config;
