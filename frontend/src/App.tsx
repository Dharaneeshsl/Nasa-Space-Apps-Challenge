import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Ask } from './pages/Ask';
import { Compare } from './pages/Compare';
import { SafetyBrief } from './pages/SafetyBrief';
import { Footer } from './components/Footer';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-[#0B0F19] text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
          {/* Global Navigation Header */}
          <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur sticky top-0 z-50">
            <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xl">🔥</span>
                <div>
                  <span className="font-bold tracking-tight text-white text-base">
                    CombustionLens
                  </span>
                  <span className="text-[10px] uppercase font-mono tracking-widest text-blue-400 block -mt-0.5">
                    NASA Space Apps 2026
                  </span>
                </div>
              </div>

              {/* Navigation Links */}
              <nav className="flex items-center gap-1 sm:gap-2 text-sm font-medium">
                <NavLink
                  to="/ask"
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-900'
                    }`
                  }
                >
                  1. Ask
                </NavLink>

                <NavLink
                  to="/compare"
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-900'
                    }`
                  }
                >
                  2. Compare
                </NavLink>

                <NavLink
                  to="/brief"
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-900'
                    }`
                  }
                >
                  3. Safety Brief
                </NavLink>
              </nav>
            </div>
          </header>

          {/* Main View Container */}
          <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Navigate to="/ask" replace />} />
              <Route path="/ask" element={<Ask />} />
              <Route path="/compare" element={<Compare />} />
              <Route path="/brief" element={<SafetyBrief />} />
              <Route path="*" element={<Navigate to="/ask" replace />} />
            </Routes>
          </main>

          {/* Global Footer (with live /api/status telemetry on every view) */}
          <Footer />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
