# SLT Telecom API Bridge - Frontend

A simple and clean Next.js frontend application that connects to the SLT Telecom API Bridge backend. Features a products table and AI chat assistant for querying telecom products.

## Features

- **📊 Products Table**: Real-time display of SLT telecom products
- **🤖 AI Chat Assistant**: Natural language queries for product information
- **🔍 Search & Filter**: Easy product search and filtering
- **📱 Responsive Design**: Works on desktop and mobile devices
- **⚡ Real-time Updates**: Live data from the backend API

## SLT Products Included

- Fiber Broadband (100Mbps)
- PeoTV Entertainment Package
- SLT Mobitel 4G SIM Card
- WiFi Router HUAWEI HG8145V5
- SLT Fixed Line Service
- SLT Business Internet (1Gbps)
- PeoTV Set-Top Box
- SLT Cloud Storage (1TB)

## Quick Start

### Prerequisites

1. **Backend Running**: Make sure the SLT API Bridge backend is running on `http://localhost:8001`
2. **Node.js**: Version 18 or higher

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at: `http://localhost:3000`

## Backend Connection

The frontend connects to your backend at `http://localhost:8001`. Make sure:

1. **Backend is running** on port 8001
2. **CORS is enabled** (already configured in your backend)
3. **Products endpoint** is accessible at `/api/v1/Products_DB`

## Usage Examples

### Chat Assistant Queries

- "Show me fiber products"
- "What mobile services do you have?"
- "Tell me about PeoTV"
- "List all broadband options"
- "What routers are available?"

## Project Structure

```
src/
├── app/
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # App layout
│   └── page.tsx           # Main page
├── components/
│   ├── ProductsTable.tsx  # Products data table
│   ├── SimpleChat.tsx     # Chat interface
│   └── ui/               # UI components
├── lib/
│   ├── api.ts            # Backend API client
│   ├── store.ts          # Zustand store
│   └── utils.ts          # Utility functions
└── types/
    └── chat.ts           # TypeScript types
```

## Development

```bash
# Development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

**Note**: This frontend is specifically designed to work with the SLT Telecom API Bridge backend. Make sure both applications are running for full functionality.

## Screenshots

- Products table with search and filtering
- Chat interface with natural language queries
- Responsive design for mobile and desktop
- Real-time data updates from backend API
