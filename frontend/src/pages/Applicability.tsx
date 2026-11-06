import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { findings, Mission, missions } from '../lib/mission';
import { ResearchPlan } from '../components/ResearchPlan';
import { assessApplicability, defaultScenario, exportAssessment, FuelClass, researchQuestion, validateScenario } from '../lib/applicability';

export function Applicability() {
  const [scenario, setScenario] = useState(defaultScenario);
  const [params] = useSearchParams();
  useEffect(() => {
    const mission = params.get('mission');
    if (mission === 'orbital' || mission === 'lunar' || mission === 'transit') {
      setScenario(prev => ({ ...prev, mission }));
    }
  }, [params]);
  const [notice, setNotice] = useState('');
  const errors = validateScenario(scenario);
  const question = researchQuestion(scenario);

  function download() {
    const url = URL.createObjectURL(new Blob([exportAssessment(scenario)], { type: 'text/markdown;charset=utf-8' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'combustionlens-applicability.md';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice('Assessment downloaded with all source links and unknown conditions.');
  }

  return (
    <div className="mission-page space-y-8 max-w-5xl mx-auto">
      {/* Telemetry Status Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-slate-800/80 bg-slate-950/70 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-sm shadow-cyan-400/50" />
          <span className="text-slate-300 font-semibold">WORKBENCH: BOUNDARY MATRIX AUDIT</span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span>TARGET MISSION: <strong className="text-amber-400 uppercase">{missions[scenario.mission].name}</strong></span>
          <span className="text-slate-700">|</span>
          <span>CHECK MODE: <strong className="text-slate-200">6-AXIS FLIGHT BOUNDARY</strong></span>
        </div>
      </div>

      <div>
        <div className="eyebrow text-amber-400">MISSION APPLICABILITY / BOUNDARY CHECKS</div>
        <h1 className="text-3xl font-bold tracking-tight text-white mt-2">
          Does this evidence travel to your mission?
        </h1>
        <p className="text-slate-400 mt-2 max-w-3xl leading-relaxed text-sm">
          Change your research scenario and inspect which experimental boundaries align, which differ, and which remain unknown. This is an evidence-gap assessment, not a fire risk prediction.
        </p>
      </div>

      {/* Target Parameters Panel */}
      <section className="scenario-panel shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4">
          <h2 className="text-lg font-semibold text-white">Define a research target</h2>
          <span className="text-xs font-mono text-slate-500">PARAM_SET: USER_TARGET</span>
        </div>
        <p className="text-xs text-slate-400">
          Optional atmosphere inputs describe your question. They are not recommended operating conditions.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
          <label className="boundary-field">
            <span>Mission</span>
            <select
              value={scenario.mission}
              onChange={e => {
                setNotice('');
                setScenario({ ...scenario, mission: e.target.value as Mission });
              }}
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            >
              {(Object.keys(missions) as Mission[]).map(m => (
                <option key={m} value={m}>{missions[m].name}</option>
              ))}
            </select>
          </label>
          <label className="boundary-field">
            <span>Fuel class</span>
            <select
              value={scenario.fuel}
              onChange={e => {
                setNotice('');
                setScenario({ ...scenario, fuel: e.target.value as FuelClass });
              }}
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="solid">Solid materials</option>
              <option value="droplet">Liquid droplets</option>
              <option value="unspecified">Unspecified</option>
            </select>
          </label>
          <label className="boundary-field">
            <span>Oxygen (% by volume)</span>
            <input
              inputMode="decimal"
              value={scenario.oxygen}
              placeholder="Unspecified"
              onChange={e => {
                setNotice('');
                setScenario({ ...scenario, oxygen: e.target.value });
              }}
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            />
          </label>
          <label className="boundary-field">
            <span>Total pressure (kPa)</span>
            <input
              inputMode="decimal"
              value={scenario.pressure}
              placeholder="Unspecified"
              onChange={e => {
                setNotice('');
                setScenario({ ...scenario, pressure: e.target.value });
              }}
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            />
          </label>
          <label className="boundary-field">
            <span>Flow regime</span>
            <select
              value={scenario.flow}
              onChange={e => {
                setNotice('');
                setScenario({ ...scenario, flow: e.target.value });
              }}
              className="focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="">Unspecified</option>
              <option value="quiescent">Quiescent</option>
              <option value="forced">Forced</option>
            </select>
          </label>
        </div>
        {errors.length > 0 && (
          <div role="alert" className="mt-4 p-3.5 rounded-lg border border-red-800/80 bg-red-950/40 text-red-200 text-xs font-mono space-y-1">
            <div className="font-bold text-red-300">INPUT VALIDATION FAILED:</div>
            {errors.map(e => (
              <p key={e}>• {e}</p>
            ))}
          </div>
        )}
      </section>

      {/* Coverage Matrix Table */}
      <section className="space-y-3">
        <div className="flex flex-wrap justify-between items-center gap-3">
          <div>
            <h2 className="text-lg font-semibold text-white">Evidence coverage matrix</h2>
            <p className="text-xs text-slate-400 mt-0.5">Click any matrix cell to review transfer rationale.</p>
          </div>
          <span className="text-xs font-mono text-amber-300/80 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
            Aligned ≠ validated · Unknown ≠ safe
          </span>
        </div>
        <div className="overflow-x-auto border border-slate-800/90 rounded-2xl bg-slate-900/60 shadow-xl backdrop-blur-md">
          <table className="boundary-table">
            <caption className="sr-only">Campaign applicability by physical boundary</caption>
            <thead>
              <tr>
                <th scope="col" className="font-mono text-slate-300">NASA campaign</th>
                {assessApplicability(scenario, 'flex').map(c => (
                  <th scope="col" key={c.condition} className="font-mono text-slate-300">{c.condition}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {findings.map(f => (
                <tr key={f.id} className="transition-colors hover:bg-slate-800/40">
                  <th scope="row" className="font-mono">
                    <a href={f.source} target="_blank" rel="noreferrer" className="text-amber-400 hover:text-amber-300 transition-colors">
                      {f.campaign} ↗
                    </a>
                  </th>
                  {assessApplicability(scenario, f.id).map(c => (
                    <td key={c.condition}>
                      <details className="cursor-pointer">
                        <summary className={`boundary-${c.status} font-mono font-medium text-xs`}>
                          {c.status === 'aligned' ? '≈ Aligned' : c.status === 'mismatch' ? '≠ Mismatch' : '? Unknown'}
                        </summary>
                        <p className="text-xs text-slate-400 mt-2 min-w-36 leading-relaxed bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
                          {c.explanation}
                        </p>
                      </details>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500 font-mono">
          Expand any cell for the reason. No run-level oxygen, pressure, ventilation or geometry match can be established from these summaries.
        </p>
      </section>

      {/* Research Plan Component */}
      {errors.length === 0 && <ResearchPlan scenario={scenario} />}

      {/* Next Research Step */}
      <section className="scenario-panel shadow-xl space-y-4">
        <div>
          <div className="eyebrow text-amber-400">NEXT RESEARCH STEP</div>
          <h2 className="text-lg font-semibold text-white mt-1">Ask the missing question.</h2>
        </div>
        <p className="text-slate-200 leading-relaxed text-sm bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 font-sans">
          "{question}"
        </p>
        <div className="flex flex-wrap gap-4 items-center pt-2">
          <button
            className="mission-primary cursor-pointer disabled:cursor-not-allowed"
            onClick={download}
            disabled={errors.length > 0}
          >
            Export applicability assessment ↓
          </button>
          {errors.length === 0 && (
            <Link
              className="text-sm font-semibold text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1.5"
              to={`/ask?q=${encodeURIComponent(question)}`}
            >
              <span>Investigate in literature workspace</span>
              <span aria-hidden="true">↗</span>
            </Link>
          )}
        </div>
        {notice && (
          <p role="status" className="text-xs font-mono text-emerald-300 mt-2 flex items-center gap-1.5">
            <span>✓</span>
            <span>{notice}</span>
          </p>
        )}
        <p className="text-xs text-slate-500 font-mono border-t border-slate-800/60 pt-3">
          Literature retrieval requires the backend and indexed primary sources. The boundary workbench runs locally without an AI model.
        </p>
      </section>
    </div>
  );
}
