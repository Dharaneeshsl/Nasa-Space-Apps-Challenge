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

  const expA = experiments.find((e) => e.staging_id === Number(selectedA));
  const expB = experiments.find((e) => e.staging_id === Number(selectedB));
  const result = compareMutation.data;

  if (isLoading) {
    return (
      <div className="p-8 text-center text-slate-400 font-mono text-sm animate-pulse">
        Loading verified experiments from DuckDB...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 text-center text-red-400 font-mono text-sm bg-red-950/20 border border-red-900/40 rounded-xl space-y-2">
        <div className="font-bold">Database / API Connection Error</div>
        <div>Failed to load verified experiments: {(error as Error)?.message || 'Unknown network error'}</div>
      </div>
    );
  }

  if (experiments.length === 0) {
    return (
      <EmptyState
        title="No Human-Verified Experiments Available Yet"
        description="The experiments database currently contains 0 verified rows. In accordance with Hard Rule #3, LLMs never extract numbers into this table; only two-person verified records will appear."
        actionText="Curate rows in data/experiments_staging.csv and run scripts/load_experiments.py"
      />
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          <span>⚖️</span> Scientific Experiment Comparator
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Direct comparative analysis over human-verified DuckDB records, governed by deterministic physical regime guardrails.
        </p>
      </div>

      {/* Selectors */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Select Two Verified Experiments to Evaluate
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="select-exp-a" className="block text-xs font-mono text-slate-400 mb-1">
              Experiment A:
            </label>
            <select
              id="select-exp-a"
              value={selectedA}
              onChange={(e) => setSelectedA(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="">-- Choose verified experiment --</option>
              {experiments.map((e) => (
                <option key={e.staging_id} value={e.staging_id}>
                  [{e.staging_id}] {e.experiment_series} • {e.fuel} ({e.metric_name})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="select-exp-b" className="block text-xs font-mono text-slate-400 mb-1">
              Experiment B:
            </label>
            <select
              id="select-exp-b"
              value={selectedB}
              onChange={(e) => setSelectedB(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
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
          className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-semibold text-sm transition-colors shadow-lg shadow-blue-900/30"
        >
          {compareMutation.isPending ? 'Evaluating Scientific Guardrails...' : 'Execute Scientific Comparability Check'}
        </button>

        {compareMutation.isError && (
          <div className="p-3 rounded-lg border border-red-900/40 bg-red-950/30 text-red-300 text-xs font-mono">
            Comparison Error: {compareMutation.error.message}
          </div>
        )}
      </div>

      {/* Side-by-Side Spec Cards */}
      {(expA || expB) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 text-xs space-y-2.5">
            <h3 className="font-bold text-sm text-blue-400">
              Experiment A: {expA?.experiment_series || 'Unselected'}
            </h3>
            <div className="space-y-1.5 divide-y divide-slate-800/80">
              <div className="flex justify-between py-1"><span>Fuel / Class:</span> <span><VerifiedValue value={expA?.fuel} /> (<VerifiedValue value={expA?.fuel_class} />)</span></div>
              <div className="flex justify-between py-1"><span>Geometry:</span> <span><VerifiedValue value={expA?.geometry} /></span></div>
              <div className="flex justify-between py-1"><span>Gravity:</span> <span><VerifiedValue value={expA?.gravity_level} /></span></div>
              <div className="flex justify-between py-1"><span>Flow Regime:</span> <span><VerifiedValue value={expA?.flow_regime} /></span></div>
              <div className="flex justify-between py-1"><span>Oxygen Level:</span> <span><VerifiedValue value={expA?.O2_value} /> (<VerifiedValue value={expA?.O2_basis} />)</span></div>
              <div className="flex justify-between py-1"><span>Standardized Pressure:</span> <span><VerifiedValue value={expA?.pressure_std_kPa} suffix="kPa" /></span></div>
              <div className="flex justify-between py-1"><span>Scale:</span> <span><VerifiedValue value={expA?.scale_dimension_raw} /></span></div>
              <div className="flex justify-between py-1"><span>Metric / Value:</span> <span><VerifiedValue value={expA?.metric_name} /> = <VerifiedValue value={expA?.metric_value_std} /> <VerifiedValue value={expA?.metric_unit_std} /></span></div>
              <div className="flex justify-between py-1"><span>Uncertainty:</span> <span><VerifiedValue value={expA?.metric_uncertainty_raw} /></span></div>
              <div className="flex justify-between py-1"><span>Provenance:</span> <span className="font-mono text-slate-400"><VerifiedValue value={expA?.conversion_provenance} /></span></div>
              <div className="flex justify-between py-1"><span>Verification:</span> <span className="text-emerald-400"><VerifiedValue value={expA?.verified_by} /> on <VerifiedValue value={expA?.verified_date} /></span></div>
            </div>
          </div>

          {/* Card B */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 text-xs space-y-2.5">
            <h3 className="font-bold text-sm text-indigo-400">
              Experiment B: {expB?.experiment_series || 'Unselected'}
            </h3>
            <div className="space-y-1.5 divide-y divide-slate-800/80">
              <div className="flex justify-between py-1"><span>Fuel / Class:</span> <span><VerifiedValue value={expB?.fuel} /> (<VerifiedValue value={expB?.fuel_class} />)</span></div>
              <div className="flex justify-between py-1"><span>Geometry:</span> <span><VerifiedValue value={expB?.geometry} /></span></div>
              <div className="flex justify-between py-1"><span>Gravity:</span> <span><VerifiedValue value={expB?.gravity_level} /></span></div>
              <div className="flex justify-between py-1"><span>Flow Regime:</span> <span><VerifiedValue value={expB?.flow_regime} /></span></div>
              <div className="flex justify-between py-1"><span>Oxygen Level:</span> <span><VerifiedValue value={expB?.O2_value} /> (<VerifiedValue value={expB?.O2_basis} />)</span></div>
              <div className="flex justify-between py-1"><span>Standardized Pressure:</span> <span><VerifiedValue value={expB?.pressure_std_kPa} suffix="kPa" /></span></div>
              <div className="flex justify-between py-1"><span>Scale:</span> <span><VerifiedValue value={expB?.scale_dimension_raw} /></span></div>
              <div className="flex justify-between py-1"><span>Metric / Value:</span> <span><VerifiedValue value={expB?.metric_name} /> = <VerifiedValue value={expB?.metric_value_std} /> <VerifiedValue value={expB?.metric_unit_std} /></span></div>
              <div className="flex justify-between py-1"><span>Uncertainty:</span> <span><VerifiedValue value={expB?.metric_uncertainty_raw} /></span></div>
              <div className="flex justify-between py-1"><span>Provenance:</span> <span className="font-mono text-slate-400"><VerifiedValue value={expB?.conversion_provenance} /></span></div>
              <div className="flex justify-between py-1"><span>Verification:</span> <span className="text-emerald-400"><VerifiedValue value={expB?.verified_by} /> on <VerifiedValue value={expB?.verified_date} /></span></div>
            </div>
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {result && (
        <div className="space-y-6">
          <GuardrailCard
            state={result.state}
            checks={result.checks}
          />

          {result.state !== 'GUARDRAIL_FAILURE' && (
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
          )}
        </div>
      )}
    </div>
  );
};
