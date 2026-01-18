# Frontend

React + TypeScript frontend for the Hybrid RAG Q&A System.

## Features

- **User Authentication** - Login/Register with JWT token management
- **Drawing Editor** - JSON editor for building drawings with syntax highlighting
- **Chat Interface** - Real-time Q&A with AI Agent
- **AI Mode Toggle** - Switch between Standard (⚡) and Agentic (🤖) modes
- **Source Citations** - View all retrieved sources with relevance scores
- **Auto Logout** - Automatic logout on JWT token expiration
- **Responsive Design** - Works on desktop and mobile devices

## Quick Start (Docker - Recommended)

The Frontend is part of the full system. See the main [README](../README.md) for complete setup.

```bash
# From project root
cd AICI
docker-compose up -d frontend
```

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Environment Variables

Create `.env` file:

```bash
REACT_APP_BACKEND_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view in browser.

## Available Scripts

### `npm start`

Runs the app in development mode on [http://localhost:3000](http://localhost:3000).

The page will reload on edits. Lint errors will show in the console.

### `npm test`

Launches the test runner in interactive watch mode.

### `npm run build`

Builds the app for production to the `build` folder.

The build is minified and filenames include hashes. Ready to deploy!

## Project Structure

```
frontend/
├── public/
│   ├── index.html           # HTML template
│   └── favicon.ico          # Favicon
├── src/
│   ├── components/          # React components
│   │   ├── Login.tsx        # Login/Register page
│   │   ├── ChatInterface.tsx # Main chat interface
│   │   └── *.css            # Component styles
│   ├── services/
│   │   └── apiClient.ts     # Backend API client
│   ├── App.tsx              # Main app component
│   ├── App.css              # App styles
│   └── index.tsx            # Entry point
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── Dockerfile               # Docker image
└── nginx.conf               # Nginx config for production
```

## Key Components

### Login Component

- User registration and login
- JWT token storage in localStorage
- Form validation
- Error handling

### Chat Interface

- Question input with submit
- Drawing JSON editor with syntax highlighting
- AI mode toggle (Standard vs Agentic)
- Message history display
- Source citations with relevance scores
- Auto-logout on token expiration

### API Client

- Centralized HTTP client for backend communication
- JWT token injection in headers
- Error handling and token expiration detection
- TypeScript types for all API requests/responses

## Configuration

Environment variables:

- `REACT_APP_BACKEND_URL` - Backend API URL (default: http://localhost:8000)

## Building for Production

```bash
# Build optimized production bundle
npm run build

# The build folder is ready to be deployed
# Serve with nginx or any static file server
```

## Docker Deployment

The Dockerfile uses multi-stage build:

1. **Build stage** - Installs dependencies and builds React app
2. **Production stage** - Serves static files with nginx

```bash
# Build image
docker build -t hybrid-rag-frontend .

# Run container
docker run -p 80:80 hybrid-rag-frontend
```

## Learn More

- [React Documentation](https://reactjs.org/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Create React App Documentation](https://facebook.github.io/create-react-app/docs/getting-started)
