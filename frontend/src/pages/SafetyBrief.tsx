import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getSafetyBrief } from '../lib/api';
import { BriefResponse } from '../lib/types';
import { TierBadge } from '../components/TierBadge';
import { CitationList } from '../components/CitationList';

const TOPIC_PRESETS = [
  {
    label: "Solid Materials Flammability",
    value: "Solid material flammability and flame spread risk in spacecraft habitats",
  },
  {
    label: "Droplet Extinction Limits",
    value: "Radiative and convective extinction limits of liquid droplet combustion in microgravity",
  },
  {
    label: "Large-Scale Fabric Combustion",
    value: "Saffire large-scale fabric flammability and low-speed ventilation flow effects",
  },
];

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

  const handleDownloadMemo = () => {
    if (!brief) return;
    const memoContent = [
      `# NASA FLIGHT SAFETY REVIEW — COMBUSTIONLENS MEMORANDUM`,
      `Document ID: MEMO-CL-SAFETY-REVIEW`,
      `Date: ${new Date().toISOString().split('T')[0]}`,
      `Evidence Tier: ${brief.tier}`,
      `Topic: ${brief.question}`,
      `Scope: ${brief.scope_statement}`,
      ``,
      `## 1. KEY LITERATURE FINDINGS & EMPIRICAL OBSERVATIONS`,
      ...brief.key_findings.map(f => `### ${f.title}\n${f.content}\nCitations: ${f.citations.map(c => `${c.paper_title || c.doc_id} (p. ${c.page})`).join(', ')}\n`),
      ``,
      `## 2. PHYSICAL CONDITIONS OF VALIDITY`,
      ...Object.entries(brief.conditions_of_validity).map(([k, v]) => `- ${k.replace(/_/g, ' ')}: ${v}`),
      ``,
      `## 3. EARTH-ANALOG MAPPING & TRANSFERABILITY`,
      brief.earth_analog_mapping,
      ``,
      `## 4. KNOWN LIMITATIONS & RESEARCH GAPS`,
      brief.limitations_and_gaps,
      ``,
      `## MANDATORY SAFETY DISCLAIMER`,
      brief.disclaimer,
    ].join('\n');

    const blob = new Blob([memoContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `combustionlens-safety-brief.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Flight Telemetry Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-slate-800/80 bg-slate-950/70 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-sm shadow-amber-400/50" />
          <span className="text-slate-300 font-semibold">PANEL: FLIGHT SAFETY REVIEW</span>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span>MODE: <strong className="text-slate-200">SYNTHESIS & VALIDITY ENVELOPES</strong></span>
          <span className="text-slate-700">|</span>
          <span>ANALOG: <strong className="text-cyan-300">BUOYANCY SUPPRESSION</strong></span>
        </div>
      </div>

      {/* Header */}
      <div>
        <div className="text-[10px] font-mono tracking-widest uppercase text-amber-400/90 mb-1">
          SPACECRAFT ENVIRONMENTAL HAZARD ASSESSMENT
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <span className="text-amber-400">📋</span> Spacecraft Fire Safety Brief
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Structured synthesis of microgravity combustion phenomenology, conditions of validity, and terrestrial translational analogs.
        </p>
      </div>

      {/* Input & Presets */}
      <div className="p-5 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-xl backdrop-blur-md space-y-4">
        <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Specify mission safety inquiry or material scenario..."
            className="flex-1 px-4 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-sm font-sans transition-all"
          />
          <button
            type="submit"
            disabled={mutation.isPending || !topic.trim()}
            className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-amber-500/20 shrink-0 flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
          >
            {mutation.isPending ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <span>Assemble Safety Brief</span>
                <span aria-hidden="true">→</span>
              </>
            )}
          </button>
        </form>

        {/* Quick Topic Chips */}
        <div className="pt-2 border-t border-slate-800/60 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500 font-mono">Suggested Scenarios:</span>
          {TOPIC_PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setTopic(preset.value);
                mutation.mutate(preset.value);
              }}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors text-left"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading state */}
      {mutation.isError && (
        <div role="alert" className="p-4 border border-red-800 rounded-xl bg-red-950/30 text-red-200 text-sm">
          Unable to assemble the brief. {mutation.error.message} Please try again when the research API is available.
        </div>
      )}

      {mutation.isPending && (
        <div className="p-8 text-center border border-slate-800 rounded-2xl bg-slate-950/80 text-slate-400 font-mono text-sm space-y-3">
          <div className="w-8 h-8 mx-auto border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-300 font-semibold">Synthesizing mission literature, extracting physical validity envelopes, and translating terrestrial analogs...</p>
          <p className="text-xs text-slate-500">Checking NASA NTRS primary sources, BASS, FLEX, and Saffire flight records</p>
        </div>
      )}

      {/* Brief Content */}
      {brief && (
        <div className="p-8 rounded-2xl border border-slate-800 bg-slate-900/70 shadow-2xl backdrop-blur-md space-y-8">
          {/* Section 1: Memo Header & Scope */}
          <div className="border-b border-slate-800 pb-5 space-y-2">
            <div className="flex flex-wrap justify-between items-center gap-3">
              <span className="text-[11px] uppercase tracking-wider font-mono text-amber-400 font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                NASA TECHNICAL MEMO · SAFETY REVIEW SYNTHESIS
              </span>
              <div className="flex items-center gap-2">
                <TierBadge tier={brief.tier} />
                <button
                  type="button"
                  onClick={handleDownloadMemo}
                  className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <span>Download Memo ↓</span>
                </button>
              </div>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white pt-1">{brief.question}</h2>
            <p className="text-xs font-mono text-slate-400 pt-1 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              {brief.scope_statement}
            </p>
          </div>

          {/* Section 2: Key Findings */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200 flex items-center gap-2 font-mono">
              <span className="text-amber-400">📌</span> 1. Key Literature Findings & Empirical Observations
            </h3>
            <div className="space-y-3">
              {brief.key_findings.map((f, idx) => (
                <div key={idx} className="p-5 rounded-xl border border-slate-800/90 bg-slate-950/70 space-y-2.5 transition-all hover:border-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      ITEM #{String(idx + 1).padStart(2, '0')}
                    </span>
                    <h4 className="text-sm font-bold text-slate-100">{f.title}</h4>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed pl-1">{f.content}</p>
                  <div className="pt-2 pl-1">
                    <CitationList citations={f.citations} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Conditions of Validity */}
          <div className="p-6 rounded-xl border border-slate-800/90 bg-slate-950/60 space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-200 flex items-center gap-2 font-mono">
              <span className="text-cyan-400">📏</span> 2. Physical Conditions of Validity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              {Object.entries(brief.conditions_of_validity).map(([k, v]) => (
                <div key={k} className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800/90 space-y-1">
                  <span className="text-slate-400 block text-[11px] uppercase tracking-wider capitalize">{k.replace(/_/g, ' ')}:</span>
                  <strong className="text-slate-100 text-sm font-semibold">{String(v)}</strong>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Earth-Analog Mapping */}
          <div className="p-6 rounded-xl border border-amber-900/50 bg-amber-950/20 space-y-2.5">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-300 flex items-center gap-2 font-mono">
              <span className="text-amber-400">🌍</span> 3. Earth-Analog Mapping & Transferability
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-mono bg-slate-950/50 p-3.5 rounded-lg border border-amber-900/30">
              {brief.earth_analog_mapping}
            </p>
          </div>

          {/* Section 5: Limitations */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-950/40 text-xs text-slate-400 space-y-2">
            <h4 className="font-semibold text-slate-200 font-mono uppercase tracking-wider text-xs">
              4. Known Limitations & Research Gaps:
            </h4>
            <p className="leading-relaxed text-slate-300 font-mono text-xs">{brief.limitations_and_gaps}</p>
          </div>

          {/* Section 6: Non-Operational Disclaimer */}
          <div className="p-4 rounded-xl border border-red-900/50 bg-red-950/30 text-red-200 text-xs leading-relaxed space-y-1">
            <div className="font-mono font-bold text-red-300 uppercase tracking-wider">
              Mandatory Safety Disclaimer:
            </div>
            <p className="text-red-200/90">{brief.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
};
