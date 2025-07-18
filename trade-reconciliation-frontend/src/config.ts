// API configuration
export const API_CONFIG = {
  API_ENDPOINT: 'https://mdj9ch24qg.execute-api.us-east-1.amazonaws.com/dev',
  REGION: 'us-east-1'
};

// Amplify configuration
export const AMPLIFY_CONFIG = {
  API: {
    endpoints: [
      {
        name: 'tradeApi',
        endpoint: 'https://mdj9ch24qg.execute-api.us-east-1.amazonaws.com/dev',
        region: 'us-east-1',
        custom_header: async () => {
          return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          };
        }
      }
    ]
  }
};