import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getSafetyBrief } from '../lib/api';
import { BriefResponse } from '../lib/types';
import { TierBadge } from '../components/TierBadge';
import { CitationList } from '../components/CitationList';

export const SafetyBrief: React.FC = () => {
  const [topic, setTopic] = useState('Solid material flammability and flame spread risk in spacecraft habitats');

  const mutation = useMutation<BriefResponse, Error, string>({
    mutationFn: getSafetyBrief,
  });

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    mutation.mutate(topic.trim());
  };

  const brief = mutation.data;

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          <span>📋</span> Spacecraft Fire Safety Brief
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Structured synthesis of microgravity combustion phenomology, conditions of validity, and terrestrial translational analogs.
        </p>
      </div>

      {/* Input */}
      <form onSubmit={handleGenerate} className="flex gap-2">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Specify mission safety inquiry or material scenario..."
          className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
        />
        <button
          type="submit"
          disabled={mutation.isPending || !topic.trim()}
          className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-sm transition-colors shadow-lg shadow-blue-900/30 shrink-0"
        >
          {mutation.isPending ? 'Synthesizing...' : 'Assemble Safety Brief'}
        </button>
      </form>

      {/* Loading state */}
      {mutation.isPending && (
        <div className="p-8 text-center border border-slate-800 rounded-xl bg-slate-900/40 text-slate-400 font-mono text-sm animate-pulse">
          Synthesizing mission literature, extracting physical validity envelopes, and translating terrestrial analogs...
        </div>
      )}

      {/* Brief Content */}
      {brief && (
        <div className="p-8 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-8">
          {/* Section 1: Scope */}
          <div className="border-b border-slate-800 pb-5 space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-xs uppercase tracking-wider font-mono text-blue-400 font-semibold">
                Operational Safety Synthesis
              </span>
              <TierBadge tier={brief.tier} />
            </div>
            <h2 className="text-xl font-bold text-white pt-1">{brief.question}</h2>
            <p className="text-xs font-mono text-slate-400 pt-1">{brief.scope_statement}</p>
          </div>

          {/* Section 2: Key Findings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <span>📌</span> 1. Key Literature Findings & Empirical Observations
            </h3>
            <div className="space-y-3">
              {brief.key_findings.map((f, idx) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                  <h4 className="text-xs font-bold text-slate-200">{f.title}</h4>
                  <p className="text-sm text-slate-300 leading-relaxed">{f.content}</p>
                  <CitationList citations={f.citations} />
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Conditions of Validity */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-950/40 space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <span>📏</span> 2. Physical Conditions of Validity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              {Object.entries(brief.conditions_of_validity).map(([k, v]) => (
                <div key={k} className="p-2.5 rounded bg-slate-900/80 border border-slate-800/80">
                  <span className="text-slate-400 block capitalize">{k.replace(/_/g, ' ')}:</span>
                  <strong className="text-slate-200">{String(v)}</strong>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Earth-Analog Mapping */}
          <div className="p-5 rounded-xl border border-amber-900/40 bg-amber-950/20 space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-300 flex items-center gap-2">
              <span>🌍</span> 3. Earth-Analog Mapping & Transferability
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed font-mono">
              {brief.earth_analog_mapping}
            </p>
          </div>

          {/* Section 5: Limitations */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/30 text-xs text-slate-400 space-y-1">
            <h4 className="font-semibold text-slate-300">4. Known Limitations & Research Gaps:</h4>
            <p className="leading-relaxed">{brief.limitations_and_gaps}</p>
          </div>

          {/* Section 6: Non-Operational Disclaimer */}
          <div className="p-3.5 rounded-lg border border-red-900/40 bg-red-950/30 text-red-200 text-xs leading-relaxed">
            <strong>Mandatory Safety Disclaimer:</strong> {brief.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
