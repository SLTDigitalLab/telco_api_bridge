'use client';

import Image from 'next/image';
import ProductsTable from '@/components/ProductsTable';
import SimpleChat from '@/components/SimpleChat';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.05)_0%,transparent_60%),radial-gradient(circle_at_70%_80%,rgba(99,102,241,0.05)_0%,transparent_60%)] pointer-events-none" />
      
      {/* Top Navigation Bar */}
      <header className="relative z-10 backdrop-blur-sm bg-gradient-to-r from-blue-900/95 via-blue-800/95 to-blue-900/95 border-b border-blue-700/30 shadow-lg">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Image
              src="/assets/slt-mobitel-logo.png"
              alt="SLT-MOBITEL"
              width={160}
              height={50}
              className="filter drop-shadow-lg hover:scale-105 transition-transform duration-300"
              priority
            />
          </div>
          
          <div className="text-center flex-1">
            <div className="text-white text-2xl font-bold">
              SLT Telecom API Bridge
            </div>
            <div className="text-blue-200 text-sm">
              MCP-Powered DBMS System
            </div>
          </div>
          
          <div className="w-40"></div> {/* Spacer for balance */}
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-6 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
              MCP-Powered Database Assistant
            </div>
            
            <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 leading-tight">
              SLT Products Database
            </h3>
            
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Query the telecom products database using natural language. Do the day today database management tasks easily and many more.
            </p>
          </div>

          {/* Products Table */}
          <div className="mb-8">
            <ProductsTable />
          </div>

          {/* Chat Interface */}
          <div className="max-w-4xl mx-auto">
            <SimpleChat />
          </div>
        </div>
      </main>
    </div>
  );
}
