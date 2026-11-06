import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FlameStudy } from '../components/FlameStudy';
import { DemoGuide } from '../components/DemoGuide';
import { useDraft } from '../lib/workspace';
import { buildBrief, findings, Focus, Mission, missions, rankFindings } from '../lib/mission';

export function MissionControl() {
  const [params] = useSearchParams();
  const [mission, setMission] = useDraft<Mission>('mission', 'orbital', (v): v is Mission => v === 'orbital' || v === 'lunar' || v === 'transit');
  const [focus, setFocus] = useState<Focus>('all');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useDraft<string[]>('selected', [], (v): v is string[] => Array.isArray(v) && v.every(id => typeof id === 'string' && findings.some(f => f.id === id)));

  useEffect(() => {
    const target = params.get('focus');
    if (target === 'materials' || target === 'detection' || target === 'atmosphere') {
      setFocus(target);
    }
  }, [params]);

  const [exported, setExported] = useState(false);
  const rows = rankFindings(focus, query);

  function toggle(id: string) {
    setExported(false);
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  function download() {
    const url = URL.createObjectURL(new Blob([buildBrief(mission, focus, findings.filter(f => selected.includes(f.id)))], { type: 'text/markdown;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `combustionlens-${mission}-brief.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setExported(true);
  }

  return (
    <div className="mission-page space-y-10">
      {/* Flight Telemetry Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-slate-800/80 bg-slate-950/70 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-sm shadow-amber-400/50" />
          <span className="text-slate-300 font-semibold">MISSION CONTROL CONSOLE</span>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-[11px]">
          <span>TRACK: <strong className="text-slate-200">FLAME IN FREEFALL</strong></span>
          <span className="hidden sm:inline text-slate-700">|</span>
          <span>CORPUS: <strong className="text-amber-400 uppercase">{findings.length} FLIGHT CAMPAIGNS</strong></span>
          <span className="hidden sm:inline text-slate-700">|</span>
          <span>MODE: <strong className="text-emerald-400">EMPIRICAL GROUNDED</strong></span>
        </div>
      </div>

      {/* Hero Section */}
      <section className="mission-hero">
        <div className="hero-copy">
          <div className="eyebrow text-amber-400">FLAME IN FREEFALL / EVIDENCE EXPLORER</div>
          <h1>
            Fire changes<br />in space.<br />
            <span>Know what<br />carries over.</span>
          </h1>
          <p>
            Explore what NASA combustion research tells us, where it applies, and what we still need to know before the next mission.
          </p>
          <a href="#evidence" className="mission-primary">
            Explore the evidence <span aria-hidden="true">↗</span>
          </a>
          <div className="hero-note flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>NASA sources · Explainable ranking · Explicit evidence gaps</span>
          </div>
        </div>
        <FlameStudy />
      </section>

      {/* Mission Stats Row */}
      <div className="mission-stats">
        <div>
          <strong>{findings.length.toString().padStart(2, '0')}<small> / CAMPAIGNS</small></strong>
          <span>Trace each finding to NASA</span>
        </div>
        <div>
          <strong>03<small> / CONTEXTS</small></strong>
          <span>Orbit, lunar surface, Mars transit</span>
        </div>
        <div>
          <strong>06<small> / BOUNDARIES</small></strong>
          <span>Inspect what matches and what is missing</span>
        </div>
        <div>
          <strong>01<small> / AUDIT TRAIL</small></strong>
          <span>Observation → limitation → next question</span>
        </div>
      </div>

      <DemoGuide />

      {/* 01: Define the Context */}
      <section className="scenario-panel shadow-xl" aria-labelledby="scenario-title">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div>
            <div className="eyebrow text-amber-400">01 / DEFINE THE CONTEXT</div>
            <h2 id="scenario-title" className="text-xl font-bold text-white mt-1">Where is your mission going?</h2>
          </div>
          <span className="text-xs font-mono text-slate-500">ENV_SELECTOR</span>
        </div>
        <div className="scenario-options">
          {(Object.keys(missions) as Mission[]).map(key => (
            <button
              key={key}
              aria-pressed={mission === key}
              className={mission === key ? 'scenario active ring-1 ring-amber-500/50' : 'scenario'}
              onClick={() => {
                setMission(key);
                setExported(false);
              }}
            >
              <strong>{missions[key].name}</strong>
              <span>{missions[key].context}</span>
            </button>
          ))}
        </div>
        <div className="transfer-note bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <span aria-hidden="true" className="text-amber-400 font-bold">↳</span>
          <p>
            <strong>Transferability boundary</strong> {missions[mission].gap}
          </p>
        </div>
        <Link className="scenario-next text-amber-400 hover:text-amber-300 font-medium" to={`/applicability?mission=${mission}`}>
          <span>Inspect the physical boundary checks</span>
          <span aria-hidden="true">↗</span>
        </Link>
      </section>

      {/* 02: Follow the Evidence */}
      <section id="evidence" className="evidence-section" aria-labelledby="evidence-title">
        <div className="evidence-heading">
          <div>
            <div className="eyebrow text-amber-400">02 / FOLLOW THE EVIDENCE</div>
            <h2 id="evidence-title" className="text-2xl font-bold text-white mt-1">From finding to research priority.</h2>
          </div>
          <span className="mode-tag bg-slate-900 border border-emerald-500/40 text-emerald-300 font-mono">
            CURATED EXPLORER · NO MODEL REQUIRED
          </span>
        </div>
        <div className="evidence-toolbar">
          <label className="search-label">
            <span>Search findings</span>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Try ventilation, oxygen, FLEX…"
              type="search"
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            />
          </label>
          <label>
            <span>Prioritize a research focus</span>
            <select
              value={focus}
              onChange={e => {
                setFocus(e.target.value as Focus);
                setExported(false);
              }}
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="all">All research</option>
              <option value="materials">Materials & flame spread</option>
              <option value="detection">Detection & extinction</option>
              <option value="atmosphere">Cabin atmosphere</option>
            </select>
          </label>
        </div>
        <details className="ranking-method">
          <summary className="text-xs font-mono text-amber-400/90 hover:text-amber-300">
            How is this ranked?
          </summary>
          <p className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800 text-xs text-slate-300 mt-2">
            Focus match: +4. Up to three distinct search-word matches: +1 each. Published observation: +1. Ties use stable card identifiers. This is a transparent editorial relevance score, not a probability, risk score, or measure of scientific confidence. Mission selection changes transferability guidance, not the underlying evidence. All cards are NASA web summaries, not independently verified experimental records.
          </p>
        </details>
        <div className="evidence-layout mt-6">
          <div className="finding-list" aria-live="polite">
            {rows.length === 0 && (
              <div className="finding-card border-dashed">
                <h3>No matching evidence in this collection.</h3>
                <p>Try a broader term. No conclusion can be drawn from an empty result.</p>
                <button className="text-action font-mono text-xs cursor-pointer" onClick={() => setQuery('')}>
                  Clear search
                </button>
              </div>
            )}
            {rows.map((f, i) => (
              <article className="finding-card shadow-lg hover:shadow-2xl transition-all" key={f.id}>
                <div className="card-top">
                  <span className="campaign-label font-mono font-bold">
                    {String(i + 1).padStart(2, '0')} / {f.campaign}
                  </span>
                  <span className="font-mono text-xs text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
                    {f.kind}
                  </span>
                </div>
                <h3>{f.title}</h3>
                <p>{f.observation}</p>
                <div className="interpretation">
                  <span>RESEARCH IMPLICATION · TEAM INTERPRETATION</span>
                  <p>{f.implication}</p>
                </div>
                <details className="cursor-pointer">
                  <summary className="font-mono text-xs text-slate-400 hover:text-slate-200">
                    Evidence boundary & ranking · {f.score} points
                  </summary>
                  <p className="font-sans text-xs text-slate-300 mt-2">{f.gap}</p>
                  <p className="font-mono text-[11px] text-slate-400 mt-1">{f.reasons.join(' · ')}</p>
                </details>
                <div className="card-footer">
                  <a
                    href={f.source}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Read source: ${f.sourceTitle}`}
                    className="font-medium hover:text-amber-300 transition-colors"
                  >
                    Read NASA source ↗
                  </a>
                  <button
                    onClick={() => toggle(f.id)}
                    aria-pressed={selected.includes(f.id)}
                    className="cursor-pointer font-medium transition-all"
                  >
                    {selected.includes(f.id) ? '✓ In your brief' : '+ Add to brief'}
                  </button>
                </div>
              </article>
            ))}
          </div>
          <aside className="brief-builder shadow-2xl">
            <div className="eyebrow text-amber-400">03 / TAKE THE EVIDENCE WITH YOU</div>
            <h2 className="text-xl font-bold text-white mt-1">Your mission brief.</h2>
            <p>Keep the finding, interpretation, limitation and original source together.</p>
            <div className="brief-count">
              {selected.length}
              <span>findings selected</span>
            </div>
            <ul>
              {findings.filter(f => selected.includes(f.id)).map(f => (
                <li key={f.id}>
                  <span>{f.campaign}</span>
                  <button
                    aria-label={`Remove ${f.campaign} from brief`}
                    onClick={() => toggle(f.id)}
                    className="text-slate-400 hover:text-red-400 cursor-pointer"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
            <button
              className="mission-primary cursor-pointer disabled:cursor-not-allowed mt-4"
              disabled={!selected.length}
              onClick={download}
            >
              Download research brief ↓
            </button>
            <p role="status" className="export-status font-mono">
              {exported ? 'Brief downloaded as Markdown.' : 'Select findings to create a portable, source-linked brief.'}
            </p>
            <div className="next-step">
              <strong className="text-white font-mono text-xs uppercase tracking-wider">Go deeper</strong>
              <Link to="/ask" className="hover:text-amber-300 transition-colors">Ask the indexed literature ↗</Link>
              <Link to="/compare" className="hover:text-amber-300 transition-colors">Compare verified experiments ↗</Link>
              <span className="text-xs text-slate-400">These tools require a populated research corpus. The explorer remains available offline.</span>
            </div>
          </aside>
        </div>
      </section>

      <p className="mission-disclaimer border-t border-slate-800/80 pt-6">
        Research prototype, not flight-qualified guidance. Source summaries checked November 6, 2026. No risk prediction or numerical safety limit is inferred from these cards.
      </p>
    </div>
  );
}
