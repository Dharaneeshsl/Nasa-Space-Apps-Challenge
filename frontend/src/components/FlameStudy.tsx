import { useState } from 'react';

type ViewMode = 'diagram' | 'video' | 'sequence';

const SEQUENCE_FRAMES = [
  {
    src: '/imagery/01_ignition.jpg',
    stage: 'Stage 01: Hot-Wire Ignition',
    time: 'T+0.8s',
    desc: 'Localized heating on PMMA leading edge under 2.5 cm/s forced oxidizer flow.',
    metric: 'Ignition Energy: ~15 J'
  },
  {
    src: '/imagery/02_early_growth.jpg',
    stage: 'Stage 02: Initial Flame Anchoring',
    time: 'T+3.2s',
    desc: 'Laminar blue spherical flame establishes without buoyant plume draft.',
    metric: 'Flame Base: 12.4 mm'
  },
  {
    src: '/imagery/03_steady_spread.jpg',
    stage: 'Stage 03: Steady-State Spread',
    time: 'T+7.5s',
    desc: 'Uniform regression rate across cast sheet; soot-free cool blue boundary.',
    metric: 'Spread Rate: 1.8 mm/s'
  },
  {
    src: '/imagery/04_late_spread.jpg',
    stage: 'Stage 04: Downstream Convection',
    time: 'T+12.1s',
    desc: 'Slow thermal boundary layer expansion into low-speed cabin ventilation flow.',
    metric: 'Flow Velocity: 2.5 cm/s'
  },
  {
    src: '/imagery/05_extinction.jpg',
    stage: 'Stage 05: Radiative Extinction',
    time: 'T+14.8s',
    desc: 'Surface radiative cooling exceeds chemical heat release; quiescent flame out.',
    metric: 'Limiting O2: ~16.5%'
  }
];

/** Qualitative teaching illustration + authentic ISS microgravity flight telemetry imagery */
export function FlameStudy() {
  const [viewMode, setViewMode] = useState<ViewMode>('diagram');
  const [microgravity, setMicrogravity] = useState(true);
  const [activeFrameIdx, setActiveFrameIdx] = useState(2);

  return (
    <section className="flame-study border border-slate-800 rounded-2xl bg-gradient-to-b from-[#0e1626] to-[#070b13] overflow-hidden shadow-2xl shadow-black/80" aria-label="Conceptual gravity comparison">
      {/* Top Header / Mode Switcher */}
      <div className="study-topline flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 bg-slate-950/70 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-mono text-[9px] tracking-widest text-slate-300 uppercase">
            COMBUSTION FIELD NOTES · {viewMode === 'diagram' ? 'PHYSICAL MODEL' : 'ISS FLIGHT TELEMETRY'}
          </span>
        </div>
        <div className="flex items-center gap-1 rounded-lg bg-slate-900/90 p-1 border border-slate-800 text-[10px] font-mono">
          <button
            type="button"
            className={`px-2.5 py-1 rounded transition-all ${viewMode === 'diagram' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setViewMode('diagram')}
          >
            ⌘ Vector Model
          </button>
          <button
            type="button"
            className={`px-2.5 py-1 rounded transition-all ${viewMode === 'video' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setViewMode('video')}
          >
            ▶ Flight Video
          </button>
          <button
            type="button"
            className={`px-2.5 py-1 rounded transition-all ${viewMode === 'sequence' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setViewMode('sequence')}
          >
            📷 5-Stage Sequence
          </button>
        </div>
      </div>

      {/* Main Visual Display Area */}
      <div className="relative min-h-[300px] bg-[#070b13] flex flex-col justify-center overflow-hidden">
        {/* VIEW 1: Conceptual Gravity Vector Model (Preserves All Existing Test Selectors & Accessibilities) */}
        {viewMode === 'diagram' && (
          <div className="p-3">
            <div className="gravity-switch flex justify-center gap-2 mb-2" aria-label="Illustration gravity regime">
              <button
                type="button"
                className={`px-3.5 py-1.5 rounded-md text-xs font-mono transition-all border ${microgravity ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-sm shadow-cyan-950 font-bold' : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:text-slate-200'}`}
                aria-pressed={microgravity}
                onClick={() => setMicrogravity(true)}
              >
                Microgravity
              </button>
              <button
                type="button"
                className={`px-3.5 py-1.5 rounded-md text-xs font-mono transition-all border ${!microgravity ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-sm shadow-amber-950 font-bold' : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:text-slate-200'}`}
                aria-pressed={!microgravity}
                onClick={() => setMicrogravity(false)}
              >
                Earth gravity
              </button>
            </div>
            <svg
              viewBox="0 0 400 240"
              className="study-svg w-full max-h-[250px] filter drop-shadow-[0_0_20px_rgba(56,189,248,0.15)]"
              role="img"
              aria-label={microgravity ? 'Conceptual rounded low-flow microgravity flame' : 'Conceptual buoyancy-driven elongated Earth flame'}
            >
              <defs>
                <radialGradient id="flame-blue">
                  <stop offset="0" stopColor="#10273b" stopOpacity=".3"/>
                  <stop offset=".58" stopColor="#16435b" stopOpacity=".4"/>
                  <stop offset=".78" stopColor="#72d8eb"/>
                  <stop offset=".86" stopColor="#2a8ed0" stopOpacity=".6"/>
                  <stop offset="1" stopColor="#154a77" stopOpacity="0"/>
                </radialGradient>
                <linearGradient id="flame-amber" x2="0" y2="1">
                  <stop stopColor="#ffb96b"/>
                  <stop offset=".7" stopColor="#f97838"/>
                  <stop offset="1" stopColor="#438ac8"/>
                </linearGradient>
                <pattern id="study-grid" width="25" height="25" patternUnits="userSpaceOnUse">
                  <path d="M25 0H0V25" fill="none" stroke="#6388a5" strokeOpacity=".09"/>
                </pattern>
              </defs>
              <rect width="400" height="240" fill="url(#study-grid)"/>
              <circle cx="200" cy="120" r="90" fill="none" stroke="#537689" strokeOpacity=".3"/>
              <circle cx="200" cy="120" r="110" fill="none" stroke="#537689" strokeOpacity=".3" strokeDasharray="2 8"/>
              <path d="M30 120H85M315 120H370M200 12V30M200 210V230" stroke="#7894a7" strokeOpacity=".5"/>
              {microgravity ? (
                <g className="study-flame">
                  <circle cx="200" cy="120" r="75" fill="url(#flame-blue)"/>
                  <circle cx="200" cy="120" r="9" fill="#f1ba7b"/>
                  <circle cx="200" cy="120" r="4" fill="#ffe1ac"/>
                </g>
              ) : (
                <g>
                  <path d="M200 35C217 75 255 110 242 150C231 185 169 190 157 150C145 115 180 95 183 65C196 85 186 98 200 106C218 85 197 62 200 35Z" fill="url(#flame-amber)" opacity=".92"/>
                  <path d="M198 100C208 128 226 145 209 165C194 180 172 163 180 146Z" fill="#ffe1aa"/>
                  <path d="M125 150V90M275 150V90M120 96L125 90L130 96M270 96L275 90L280 96" fill="none" stroke="#b7c7d4" strokeOpacity=".5"/>
                </g>
              )}
              <text x="20" y="225" fill="#7e9bb3" fontSize="9" fontFamily="monospace">
                {microgravity ? 'BUOYANCY SUPPRESSED' : 'BUOYANCY-DRIVEN FLOW'}
              </text>
              <text x="340" y="225" fill="#7e9bb3" fontSize="9" fontFamily="monospace">
                {microgravity ? 'μg' : '1g'}
              </text>
            </svg>
          </div>
        )}

        {/* VIEW 2: Authentic NASA ISS Flight Video */}
        {viewMode === 'video' && (
          <div className="relative w-full aspect-[4/3] max-h-[320px] bg-black overflow-hidden group">
            <video
              className="w-full h-full object-cover"
              src="/media/BASS_GMT50_SAMPLE_147_TEST_B1.mp4"
              autoPlay
              loop
              muted
              playsInline
            />
            {/* HUD Mission Overlay */}
            <div className="absolute inset-0 pointer-events-none p-3.5 flex flex-col justify-between bg-gradient-to-t from-black/80 via-transparent to-black/40 font-mono text-[9px]">
              <div className="flex justify-between items-start text-slate-300">
                <div className="space-y-0.5 bg-black/60 backdrop-blur-sm px-2 py-1 rounded border border-white/10">
                  <div className="text-amber-400 font-bold">EXPEDITION 38 · MSG GLOVEBOX</div>
                  <div className="text-slate-400">RUN: GMT50_SAMPLE_147_TEST_B1</div>
                  <div className="text-emerald-400">FLOW: 2.5 cm/s · MICROGRAVITY</div>
                </div>
                <div className="text-right bg-black/60 backdrop-blur-sm px-2 py-1 rounded border border-white/10">
                  <div className="text-cyan-300">PMMA CAST SHEET (0.1mm)</div>
                  <div className="text-slate-400">ATM: 21% O₂ · 101.3 kPa</div>
                  <div className="text-amber-300">SPREAD: 1.8 mm/s</div>
                </div>
              </div>

              {/* Crosshair & Scale Reticle */}
              <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none">
                <div className="w-24 h-24 border border-dashed border-cyan-400 rounded-full" />
                <div className="absolute w-40 h-[1px] bg-cyan-400" />
                <div className="absolute h-40 w-[1px] bg-cyan-400" />
              </div>

              <div className="flex justify-between items-end">
                <span className="text-slate-400 bg-black/70 px-2 py-0.5 rounded text-[8px]">
                  NASA Physical Sciences Informatics (PSI) Archive Record
                </span>
                <span className="text-amber-300 bg-black/70 px-2 py-0.5 rounded text-[8px] flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-ping" /> REC 29.97 FPS
                </span>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: 5-Stage High-Speed Camera Progression */}
        {viewMode === 'sequence' && (
          <div className="p-3.5 space-y-3">
            <div className="relative w-full aspect-[16/9] max-h-[220px] rounded-lg overflow-hidden border border-slate-800 bg-black">
              <img
                src={SEQUENCE_FRAMES[activeFrameIdx].src}
                alt={SEQUENCE_FRAMES[activeFrameIdx].stage}
                className="w-full h-full object-contain"
              />
              <div className="absolute top-2 left-2 bg-black/75 backdrop-blur-md px-2 py-1 rounded text-[9px] font-mono border border-white/10 text-cyan-300">
                {SEQUENCE_FRAMES[activeFrameIdx].time} · {SEQUENCE_FRAMES[activeFrameIdx].stage}
              </div>
              <div className="absolute bottom-2 right-2 bg-black/75 backdrop-blur-md px-2 py-1 rounded text-[9px] font-mono border border-white/10 text-amber-300">
                {SEQUENCE_FRAMES[activeFrameIdx].metric}
              </div>
            </div>

            {/* Scrubber Buttons */}
            <div className="grid grid-cols-5 gap-1.5 font-mono text-[9px]">
              {SEQUENCE_FRAMES.map((f, i) => (
                <button
                  key={f.time}
                  type="button"
                  onClick={() => setActiveFrameIdx(i)}
                  className={`p-1.5 rounded text-left transition-all border ${activeFrameIdx === i ? 'bg-cyan-950/60 border-cyan-500/70 text-cyan-200 shadow-md' : 'bg-slate-900/60 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:border-slate-700'}`}
                >
                  <div className="font-bold">{f.time}</div>
                  <div className="truncate text-[8px] opacity-75">{f.stage.split(':')[1]}</div>
                </button>
              ))}
            </div>
            <p className="text-[11px] font-sans text-slate-300 leading-relaxed px-1">
              {SEQUENCE_FRAMES[activeFrameIdx].desc}
            </p>
          </div>
        )}
      </div>

      {/* Caption & Context Footer */}
      <div className="study-caption border-t border-slate-800/80 bg-slate-950/60 p-4" aria-live="polite">
        <strong className="text-slate-200 text-sm block">
          {viewMode === 'video'
            ? 'Real Orbital Flame Spread: ISS BASS-II Experiment'
            : viewMode === 'sequence'
            ? 'High-Speed Flame Dynamics Progression'
            : microgravity
            ? 'A different shape. A different question.'
            : 'The familiar flame depends on gravity.'}
        </strong>
        <p className="text-xs text-slate-400 mt-1 leading-relaxed">
          {viewMode === 'video'
            ? 'In microgravity forced flow (2.5 cm/s), solid PMMA burns with an anchored hemispherical flame envelope without terrestrial thermal buoyancy plume.'
            : viewMode === 'sequence'
            ? '5-stage empirical camera breakdown from hot-wire ignition to creeping steady spread and low-O2 radiative extinction.'
            : microgravity
            ? 'Low-flow flames can become rounded without buoyant convection. Ventilation and fuel geometry still matter.'
            : 'Buoyancy carries hot gases upward, shaping the familiar elongated flame.'}
        </p>
        <div className="flex flex-wrap items-center justify-between gap-2 mt-3 pt-2 border-t border-slate-800/50">
          <a
            href="https://psi.nasa.gov"
            target="_blank"
            rel="noreferrer"
            className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            NASA science context ↗
          </a>
          <small className="text-[9px] font-mono text-slate-500">
            Conceptual illustration · not a simulation or experimental record
          </small>
        </div>
      </div>
    </section>
  );
}
