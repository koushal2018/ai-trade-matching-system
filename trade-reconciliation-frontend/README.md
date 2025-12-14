# Trade Reconciliation Frontend

This is the frontend application for the Trade Reconciliation System, built with React, TypeScript, and AWS Amplify.

## Features

- User authentication with Amazon Cognito
- Dashboard with reconciliation metrics and charts
- Document upload for trade PDFs
- Trade exploration and matching
- Reconciliation details and reporting
- Admin settings for system configuration

## Tech Stack

- React.js with TypeScript
- AWS Amplify for authentication, API, and storage
- Tailwind CSS for styling
- Chart.js for data visualization
- React Router for navigation

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- AWS account
- AWS Amplify CLI

### Installation

1. Install the Amplify CLI globally:

```bash
npm install -g @aws-amplify/cli
```

2. Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd trade-reconciliation-frontend
npm install
```

3. Initialize Amplify in the project:

```bash
amplify init
```

Follow the prompts to configure your project.

4. Add authentication:

```bash
amplify add auth
```

Choose the default configuration or customize as needed.

5. Add storage for document uploads:

```bash
amplify add storage
```

Configure S3 storage with appropriate permissions.

6. Add API for backend connectivity:

```bash
amplify add api
```

Configure API Gateway or AppSync as needed.

7. Push the configuration to AWS:

```bash
amplify push
```

8. Start the development server:

```bash
npm start
```

## Deployment

### Deploy with Amplify Console

1. Push your code to a Git repository (GitHub, GitLab, BitBucket, etc.)

2. Go to the AWS Amplify Console and connect your repository

3. Follow the steps to configure your build settings

4. Deploy the application

### Manual Deployment

1. Build the application:

```bash
npm run build
```

2. Deploy the build folder to Amplify:

```bash
amplify publish
```

## Project Structure

```
src/
├── components/
│   ├── auth/          # Authentication components
│   ├── layout/        # Layout components
│   ├── pages/         # Page components
│   └── ui/            # Reusable UI components
├── App.tsx            # Main application component
├── aws-exports.ts     # AWS Amplify configuration
└── index.tsx          # Application entry point
```

## Environment Variables

The following environment variables can be set in the Amplify Console:

- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_REGION`: AWS region

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a pull request

## License

This project is proprietary and confidential.