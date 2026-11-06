import React, { lazy, Suspense, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate, useLocation, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Ask } from './pages/Ask';
import { SafetyBrief } from './pages/SafetyBrief';
import { Footer } from './components/Footer';
import { MissionControl } from './pages/MissionControl';
import { Applicability } from './pages/Applicability';

const Compare = lazy(() => import('./pages/Compare').then(m => ({ default: m.Compare })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 300000,
      retry: 1
    }
  }
});

const destinations = [
  { path: '/', title: 'Evidence explorer', short: 'Explore', symbol: '◉', number: '01', desc: 'NASA flight findings' },
  { path: '/applicability', title: 'Mission applicability', short: 'Boundaries', symbol: '⌘', number: '02', desc: 'Regime boundary checks' },
  { path: '/ask', title: 'Ask the literature', short: 'Ask', symbol: '⌕', number: '03', desc: 'Grounded citation search' },
  { path: '/compare', title: 'Compare experiments', short: 'Compare', symbol: '⇄', number: '04', desc: 'Regime guardrails & data' },
  { path: '/brief', title: 'Safety synthesis', short: 'Synthesis', symbol: '▤', number: '05', desc: 'Structured flight brief' },
];

function Workspace() {
  const { pathname } = useLocation();
  const current = destinations.find(d => d.path === pathname);

  // Live telemetry UTC clock
  const [utcTime, setUtcTime] = useState('');
  useEffect(() => {
    const update = () => {
      const now = new Date();
      setUtcTime(now.toISOString().substring(11, 19) + ' UTC');
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="workspace-shell">
      <a className="skip-link" href="#main-content">Skip to workspace</a>

      {/* Sidebar Command Console */}
      <aside className="workspace-sidebar">
        <Link to="/" className="brand-lockup group">
          <div className="relative flex items-center justify-center">
            <img src="/mark.svg" width="36" height="36" alt="CombustionLens Emblem" className="transition-transform group-hover:scale-105" />
            <div className="absolute inset-0 rounded-full bg-cyan-400/20 blur-md -z-10 animate-pulse" />
          </div>
          <div>
            <span className="text-white font-bold tracking-tight text-base flex items-center gap-1.5">
              CombustionLens
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" />
            </span>
            <small className="text-slate-400 block font-mono text-[7px] tracking-widest uppercase">
              NASA Microgravity Research HUD
            </small>
          </div>
        </Link>

        <div className="sidebar-label">RESEARCH FLIGHT CONSOLE</div>

        <nav aria-label="Main navigation" className="space-y-1">
          {destinations.map(d => (
            <NavLink
              end={d.path === '/'}
              key={d.path}
              to={d.path}
              className={({ isActive }) => `workspace-nav group relative ${isActive ? 'selected' : ''}`}
            >
              <span className="nav-symbol text-slate-400 group-hover:text-cyan-300 transition-colors" aria-hidden="true">
                {d.symbol}
              </span>
              <span className="nav-full font-medium tracking-tight">
                {d.title}
              </span>
              <span className="nav-short">{d.short}</span>
              <small className="font-mono text-[9px] text-slate-500 group-hover:text-slate-300 ml-auto transition-colors">
                {d.number}
              </small>
            </NavLink>
          ))}
        </nav>

        {/* Sidebar Mission Focus Card */}
        <div className="sidebar-bottom">
          <div className="sidebar-mission border border-slate-800 bg-gradient-to-br from-[#121c2c] to-[#0a1019] rounded-xl p-4 shadow-lg shadow-black/40 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-xl pointer-events-none" />
            <div className="eyebrow text-[9px] text-amber-400 font-mono tracking-widest">
              THE ARTEMIS HORIZON
            </div>
            <strong className="text-sm text-slate-100 font-semibold block mt-1.5 leading-snug">
              Microgravity Fire Safety
            </strong>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
              Trace empirical findings from ISS and drop towers to lunar and Mars habitat safety envelopes.
            </p>
            <Link
              to="/applicability?mission=lunar"
              className="inline-flex items-center gap-1 text-[11px] font-mono text-cyan-400 hover:text-cyan-300 mt-3 transition-colors font-medium"
            >
              Inspect lunar boundaries <span>↗</span>
            </Link>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[9px] font-mono text-slate-500">
            <span>NASA SPACE APPS 2026</span>
            <span className="text-emerald-400/90 font-medium">PSI & NTRS ARCHIVE</span>
          </div>
          <p className="text-[9px] text-slate-600 font-mono mt-1">
            Zero-fabrication research architecture.
          </p>
        </div>
      </aside>

      {/* Main Workspace Body */}
      <div className="workspace-body">
        {/* Topbar Telemetry Header */}
        <header className="workspace-topbar border-b border-slate-800/80 bg-[#090e18]/85 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <span className="topbar-prefix text-slate-500 font-mono text-xs">Console /</span>
            <span className="text-white font-semibold tracking-tight text-sm flex items-center gap-2">
              {current?.title || 'Research'}
              <span className="text-xs font-mono font-normal text-slate-400">({current?.desc})</span>
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            {/* Live Clock Pill */}
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-900/90 border border-slate-800 text-slate-300 text-[10px]">
              <span className="text-slate-500">SYS CLOCK:</span>
              <span className="text-cyan-300 font-bold">{utcTime || '12:00:00 UTC'}</span>
            </div>

            {/* Curated status badge with pulse */}
            <span className="workspace-status px-2.5 py-1 rounded-md bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 text-[10px] flex items-center gap-2 font-mono">
              <i className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              CURATED RESEARCH DEMO
            </span>
          </div>
        </header>

        {/* Page Content */}
        <main id="main-content" tabIndex={-1} className="workspace-content">
          <Suspense fallback={
            <div className="p-16 text-center space-y-3 font-mono text-sm text-slate-400 animate-pulse">
              <div className="w-8 h-8 mx-auto rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
              <p role="status">Initializing mission research workspace…</p>
            </div>
          }>
            <Routes>
              <Route path="/" element={<MissionControl />} />
              <Route path="/applicability" element={<Applicability />} />
              <Route path="/ask" element={<Ask />} />
              <Route path="/compare" element={<Compare />} />
              <Route path="/brief" element={<SafetyBrief />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </main>

        <Footer />
      </div>
    </div>
  );
}

export const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Workspace />
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
