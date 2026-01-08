# VenezuelaWatch Frontend

React 18 + Vite + TypeScript frontend for the VenezuelaWatch real-time intelligence platform.

## Requirements

- Node.js 18+ required
- Django backend running on localhost:8000

## Setup

Install dependencies:

```bash
npm install
```

## Development

Run the development server:

```bash
npm run dev
```

This will start the Vite dev server on http://localhost:5173. The dev server automatically proxies API requests to the Django backend at localhost:8000.

## Build

Build for production:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## API Integration

The frontend is configured to communicate with the Django backend:

- **Proxy Configuration:** Vite proxies `/api/*` requests to `http://localhost:8000`
- **API Client:** Typed API client at `src/lib/api.ts` provides type-safe API methods
- **Health Check:** App includes a health check to verify backend connectivity

**Important:** Ensure the Django backend is running on localhost:8000 before starting the dev server.

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   └── api.ts          # Typed API client
│   ├── App.tsx             # Main application component
│   ├── main.tsx            # React 18 entry point
│   └── ...
├── vite.config.ts          # Vite configuration with proxy
├── tsconfig.json           # TypeScript configuration
└── package.json
```
