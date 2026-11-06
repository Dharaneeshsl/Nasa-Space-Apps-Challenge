import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getVerifiedExperiments, compareExperiments } from '../lib/api';
import { ExperimentItem, CompareResponse } from '../lib/types';
import { GuardrailCard } from '../components/GuardrailCard';
import { ErrorBarChart } from '../components/ErrorBarChart';
import { EmptyState } from '../components/EmptyState';
import { VerifiedValue } from '../components/VerifiedValue';

export const Compare: React.FC = () => {
  const [selectedA, setSelectedA] = useState<number | ''>('');
  const [selectedB, setSelectedB] = useState<number | ''>('');

  // 1. Fetch verified experiments
  const {
    data: experiments = [],
    isLoading,
    isError,
    error,
  } = useQuery<ExperimentItem[]>({
    queryKey: ['verified-experiments'],
    queryFn: getVerifiedExperiments,
  });

  // 2. Comparison mutation
  const compareMutation = useMutation<CompareResponse, Error, { id_a: number; id_b: number }>({
    mutationFn: ({ id_a, id_b }) => compareExperiments(id_a, id_b),
  });

  const handleCompare = () => {
    if (selectedA !== '' && selectedB !== '') {
      compareMutation.mutate({ id_a: Number(selectedA), id_b: Number(selectedB) });
    }
  };

  const applyPreset = (idA: number, idB: number) => {
    setSelectedA(idA);
    setSelectedB(idB);
    compareMutation.mutate({ id_a: idA, id_b: idB });
  };

  const expA = experiments.find((e) => e.staging_id === Number(selectedA));
  const expB = experiments.find((e) => e.staging_id === Number(selectedB));
  const result = compareMutation.variables?.id_a === selectedA && compareMutation.variables?.id_b === selectedB ? compareMutation.data : undefined;

  if (isLoading) {
    return (
      <div className="p-12 text-center text-slate-400 font-mono text-sm animate-pulse space-y-3">
        <div className="w-8 h-8 mx-auto rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
        <p>Loading verified experiments from DuckDB storage...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 text-center text-red-400 font-mono text-sm bg-red-950/20 border border-red-900/40 rounded-2xl space-y-2">
        <div className="font-bold text-red-300">Database / API Connection Error</div>
        <div>Failed to load verified experiments: {(error as Error)?.message || 'Unknown network error'}</div>
      </div>
    );
  }

  if (experiments.length === 0) {
    return (
      <EmptyState
        title="No Human-Verified Experiments Available Yet"
        description="Published measurements are awaiting independent review. Numerical comparisons become available after that review; explore campaign findings and mission applicability in the meantime."
        actionText="Continue with Evidence explorer or Mission applicability in the navigation."
      />
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="font-mono text-[9px] tracking-widest text-amber-400 uppercase mb-1">
              ZERO-FABRICATION COMPARATIVE HUD
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <span>⚖️</span> Scientific Experiment Comparator
            </h1>
            <p className="text-sm text-slate-400 mt-1.5 max-w-2xl leading-relaxed">
              Direct comparative analysis over human-verified DuckDB flight records. Physical guardrails deterministically prevent unphysical or mismatched regime comparisons.
            </p>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[10px] text-slate-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>DuckDB Verified Rows: <strong className="text-white">{experiments.length}</strong></span>
          </div>
        </div>

        {/* Quick Presets for Evaluators */}
        <div className="mt-5 pt-4 border-t border-slate-800/60 flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-slate-400 mr-1 flex items-center gap-1">
            <span>⚡</span> Quick Flight Test Presets:
          </span>
          <button
            type="button"
            onClick={() => applyPreset(1, 2)}
            className="text-xs px-3 py-1.5 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/50 border border-emerald-800/50 text-emerald-300 font-mono transition-all flex items-center gap-1.5"
          >
            <span>✓</span> BASS-II Spread Rate (Sample 147 vs 148) <span className="text-[10px] opacity-75">[PASS]</span>
          </button>
          <button
            type="button"
            onClick={() => applyPreset(1, 3)}
            className="text-xs px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/50 border border-rose-800/50 text-rose-300 font-mono transition-all flex items-center gap-1.5"
          >
            <span>✕</span> Geometry Conflict (Sheet vs Rod) <span className="text-[10px] opacity-75">[GUARDRAIL FAILURE]</span>
          </button>
          <button
            type="button"
            onClick={() => applyPreset(4, 5)}
            className="text-xs px-3 py-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/50 border border-cyan-800/50 text-cyan-300 font-mono transition-all flex items-center gap-1.5"
          >
            <span>✓</span> FLEX Methanol Droplets (21% vs 30% O₂) <span className="text-[10px] opacity-75">[PASS]</span>
          </button>
        </div>
      </div>

      {/* Selectors Panel */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-b from-[#111927] to-[#0c121d] space-y-5 shadow-xl shadow-black/50">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-300 font-mono flex items-center gap-2">
            <span>◉</span> Select Two Verified Experiments to Evaluate
          </h2>
          <span className="text-[10px] font-mono text-slate-400">
            Automated Physical Equivalence Check Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="space-y-1.5">
            <label htmlFor="select-exp-a" className="block text-xs font-mono text-cyan-300 font-medium">
              Experiment A (Baseline / Reference):
            </label>
            <select
              id="select-exp-a"
              value={selectedA}
              onChange={(e) => setSelectedA(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-3.5 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 font-sans shadow-inner"
            >
              <option value="">-- Choose verified experiment --</option>
              {experiments.map((e) => (
                <option key={e.staging_id} value={e.staging_id}>
                  [{e.staging_id}] {e.experiment_series} • {e.fuel} ({e.metric_name})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="select-exp-b" className="block text-xs font-mono text-indigo-300 font-medium">
              Experiment B (Comparison Target):
            </label>
            <select
              id="select-exp-b"
              value={selectedB}
              onChange={(e) => setSelectedB(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-3.5 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-sans shadow-inner"
            >
              <option value="">-- Choose verified experiment --</option>
              {experiments.map((e) => (
                <option key={e.staging_id} value={e.staging_id}>
                  [{e.staging_id}] {e.experiment_series} • {e.fuel} ({e.metric_name})
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={selectedA === '' || selectedB === '' || compareMutation.isPending}
          className="w-full py-3.5 px-5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-40 text-white font-bold text-sm transition-all shadow-lg shadow-cyan-950/60 flex items-center justify-center gap-2"
        >
          {compareMutation.isPending ? (
            <>
              <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
              <span>Evaluating Scientific Guardrails...</span>
            </>
          ) : (
            <>
              <span>⚡</span> Execute Scientific Comparability Check
            </>
          )}
        </button>

        {compareMutation.isError && (
          <div className="p-3.5 rounded-xl border border-red-900/50 bg-red-950/40 text-red-300 text-xs font-mono">
            Comparison Error: {compareMutation.error.message}
          </div>
        )}
      </div>

      {/* Side-by-Side Cockpit Spec Cards */}
      {(expA || expB) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A */}
          <div className="p-6 rounded-2xl border border-cyan-900/30 bg-gradient-to-b from-cyan-950/20 to-slate-900/50 text-xs space-y-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-cyan-900/40 pb-3">
              <h3 className="font-bold text-sm text-cyan-300 font-mono flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Experiment A: {expA?.experiment_series || 'Unselected'}
              </h3>
              {expA && (
                <span className="font-mono text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  ID: #{expA.staging_id}
                </span>
              )}
            </div>
            <div className="space-y-2 divide-y divide-slate-800/60 font-sans">
              <div className="flex justify-between py-1 text-slate-300"><span>Fuel / Class:</span> <span className="font-semibold text-white"><VerifiedValue value={expA?.fuel} /> (<VerifiedValue value={expA?.fuel_class} />)</span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Geometry:</span> <span className="font-semibold text-white"><VerifiedValue value={expA?.geometry} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Gravity:</span> <span className="font-semibold text-amber-300"><VerifiedValue value={expA?.gravity_level} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Flow Regime:</span> <span className="font-semibold text-white"><VerifiedValue value={expA?.flow_regime} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Oxygen Level:</span> <span className="font-semibold text-white"><VerifiedValue value={expA?.O2_value} /> (<VerifiedValue value={expA?.O2_basis} />)</span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Standardized Pressure:</span> <span className="font-semibold text-white"><VerifiedValue value={expA?.pressure_std_kPa} suffix="kPa" /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Scale:</span> <span className="font-semibold text-white"><VerifiedValue value={expA?.scale_dimension_raw} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Metric / Value:</span> <span className="font-semibold text-emerald-400"><VerifiedValue value={expA?.metric_name} /> = <VerifiedValue value={expA?.metric_value_std} /> <VerifiedValue value={expA?.metric_unit_std} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Uncertainty:</span> <span className="font-semibold text-slate-400"><VerifiedValue value={expA?.metric_uncertainty_raw} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Provenance:</span> <span className="font-mono text-slate-400 truncate max-w-[200px]"><VerifiedValue value={expA?.conversion_provenance} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Verification:</span> <span className="text-emerald-400 font-mono text-[10px]"><VerifiedValue value={expA?.verified_by} /> on <VerifiedValue value={expA?.verified_date} /></span></div>
            </div>
          </div>

          {/* Card B */}
          <div className="p-6 rounded-2xl border border-indigo-900/30 bg-gradient-to-b from-indigo-950/20 to-slate-900/50 text-xs space-y-3 shadow-lg">
            <div className="flex items-center justify-between border-b border-indigo-900/40 pb-3">
              <h3 className="font-bold text-sm text-indigo-300 font-mono flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-400" />
                Experiment B: {expB?.experiment_series || 'Unselected'}
              </h3>
              {expB && (
                <span className="font-mono text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  ID: #{expB.staging_id}
                </span>
              )}
            </div>
            <div className="space-y-2 divide-y divide-slate-800/60 font-sans">
              <div className="flex justify-between py-1 text-slate-300"><span>Fuel / Class:</span> <span className="font-semibold text-white"><VerifiedValue value={expB?.fuel} /> (<VerifiedValue value={expB?.fuel_class} />)</span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Geometry:</span> <span className="font-semibold text-white"><VerifiedValue value={expB?.geometry} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Gravity:</span> <span className="font-semibold text-amber-300"><VerifiedValue value={expB?.gravity_level} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Flow Regime:</span> <span className="font-semibold text-white"><VerifiedValue value={expB?.flow_regime} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Oxygen Level:</span> <span className="font-semibold text-white"><VerifiedValue value={expB?.O2_value} /> (<VerifiedValue value={expB?.O2_basis} />)</span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Standardized Pressure:</span> <span className="font-semibold text-white"><VerifiedValue value={expB?.pressure_std_kPa} suffix="kPa" /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Scale:</span> <span className="font-semibold text-white"><VerifiedValue value={expB?.scale_dimension_raw} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Metric / Value:</span> <span className="font-semibold text-emerald-400"><VerifiedValue value={expB?.metric_name} /> = <VerifiedValue value={expB?.metric_value_std} /> <VerifiedValue value={expB?.metric_unit_std} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Uncertainty:</span> <span className="font-semibold text-slate-400"><VerifiedValue value={expB?.metric_uncertainty_raw} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Provenance:</span> <span className="font-mono text-slate-400 truncate max-w-[200px]"><VerifiedValue value={expB?.conversion_provenance} /></span></div>
              <div className="flex justify-between py-1 text-slate-300"><span>Verification:</span> <span className="text-emerald-400 font-mono text-[10px]"><VerifiedValue value={expB?.verified_by} /> on <VerifiedValue value={expB?.verified_date} /></span></div>
            </div>
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {result && (
        <div className="space-y-6 pt-2">
          <GuardrailCard
            state={result.state}
            checks={result.checks}
          />

          {result.state !== 'GUARDRAIL_FAILURE' && (
            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-mono text-xs uppercase tracking-wider text-slate-300 font-bold flex items-center gap-2">
                  <span>📊</span> Harmonized Metric Visualization with Experimental Uncertainty
                </h3>
                <span className="font-mono text-[10px] text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                  Unit: {result.metric_unit || 'std'}
                </span>
              </div>
              <ErrorBarChart
                seriesA={result.series_a}
                seriesB={result.series_b}
                valueA={result.value_a}
                valueB={result.value_b}
                uncertaintyA={result.uncertainty_a}
                uncertaintyB={result.uncertainty_b}
                uncertaintyReported={result.uncertainty_reported}
                metricName={result.metric_name}
                metricUnit={result.metric_unit}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
