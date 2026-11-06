import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { askQuestion } from '../lib/api';
import { AskResponse } from '../lib/types';
import { TierBadge } from '../components/TierBadge';
import { RankBreakdown } from '../components/RankBreakdown';
import { CitationList } from '../components/CitationList';
import { RefusalCard } from '../components/RefusalCard';
import { EmptyState } from '../components/EmptyState';

const SAMPLE_QUERIES = [
  {
    category: "Droplets",
    query: "What is the droplet burning rate constant of n-heptane in microgravity under quiescent flow at 101 kPa?",
  },
  {
    category: "Flame Spread",
    query: "How does low-speed forced convection affect flame spread over PMMA in microgravity?",
  },
  {
    category: "Extinction",
    query: "What is the radiative extinction limit of spherical droplet flames?",
  },
  {
    category: "Boundary Test",
    query: "What are the flammability limits of regolith on lunar surface?",
  },
];

export const Ask: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(() => (searchParams.get('q') || '').slice(0, 500));

  const mutation = useMutation<AskResponse, Error, string>({
    mutationFn: askQuestion,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    mutation.mutate(query.trim());
  };

  const data = mutation.data;

  // Compute top relevance percentage for display
  const topRelevanceScore = data?.normalized_relevance_scores
    ? Math.max(0, ...Object.values(data.normalized_relevance_scores))
    : 0;

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Flight Telemetry Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-slate-800/80 bg-slate-950/70 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50" />
          <span className="text-slate-300 font-semibold">TERMINAL ID: CL-RETRIEVE-01</span>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-[11px]">
          <span>CORPUS: <strong className="text-slate-200">NASA NTRS INDEX</strong></span>
          <span className="hidden sm:inline text-slate-700">|</span>
          <span>RERANKER: <strong className="text-slate-200">CROSS-ENCODER BIO-PHYSICAL</strong></span>
          <span className="hidden sm:inline text-slate-700">|</span>
          <span>GATE: <strong className="text-amber-300 font-semibold">NUMBER VERIFIED</strong></span>
        </div>
      </div>

      {/* Page Header */}
      <div>
        <div className="text-[10px] font-mono tracking-widest uppercase text-amber-400/90 mb-1">
          EVIDENCE RETRIEVAL & FACT-CHECKED SYNTHESIS
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <span className="text-amber-400">🔬</span> Ask CombustionLens
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Explore indexed NASA microgravity combustion reports with page-level citations and explicit evidence limits. Zero ungrounded generation.
        </p>
      </div>

      {/* Query Console */}
      <form onSubmit={handleSubmit} className="space-y-3 p-5 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="flex justify-between items-center">
          <label htmlFor="research-query-input" className="block text-xs font-mono text-slate-400">
            Enter Research Question (max 500 characters):
          </label>
          <span className="text-[11px] font-mono text-slate-500">
            {query.length} / 500
          </span>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 font-mono text-xs">
              &gt;_
            </div>
            <input
              id="research-query-input"
              type="text"
              maxLength={500}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What is the burning rate of n-heptane droplets under microgravity?"
              className="w-full pl-9 pr-4 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 font-sans text-sm transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={mutation.isPending || !query.trim()}
            className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-amber-500/20 shrink-0 flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
          >
            {mutation.isPending ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <span>Explore Evidence</span>
                <span aria-hidden="true" className="text-xs">↗</span>
              </>
            )}
          </button>
        </div>

        {/* Sample query pills */}
        <div className="pt-2 border-t border-slate-800/60 mt-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-500 font-mono">Sample Queries:</span>
            {SAMPLE_QUERIES.map((item, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(item.query);
                  mutation.mutate(item.query);
                }}
                className="text-xs px-2.5 py-1 rounded-md bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors truncate max-w-xs flex items-center gap-1.5 text-left"
              >
                <span className="text-[10px] font-mono text-amber-400/80 uppercase font-semibold">[{item.category}]</span>
                <span className="truncate">{item.query}</span>
              </button>
            ))}
          </div>
        </div>
      </form>

      {/* Real-Time Processing Stepper */}
      {mutation.isPending && (
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2 font-mono text-xs text-amber-300">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
              <span>EXECUTING MULTI-STAGE EVIDENCE RETRIEVAL PIPELINE...</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">SYS_STAGE: IN_PROGRESS</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300">
              <div className="text-[10px] text-amber-400 font-bold mb-1">01 / DENSE SEARCH</div>
              <p className="text-slate-400 text-[11px]">Generating bi-encoder query vector & scanning embeddings</p>
            </div>
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300">
              <div className="text-[10px] text-cyan-400 font-bold mb-1">02 / LOGIT RERANK</div>
              <p className="text-slate-400 text-[11px]">Computing cross-encoder passage-query relevance scores</p>
            </div>
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300">
              <div className="text-[10px] text-emerald-400 font-bold mb-1">03 / FACT GATE</div>
              <p className="text-slate-400 text-[11px]">Checking numerical consistency against source PDFs</p>
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {mutation.isError && (
        <div className="p-5 rounded-xl border border-red-900/50 bg-red-950/30 text-red-200 text-sm space-y-2">
          <div className="font-semibold flex items-center gap-2">
            <span>⚠️</span> Query Execution Error
          </div>
          <p className="font-mono text-xs text-red-300/90 leading-relaxed">
            Failed to process query: {mutation.error.message}
          </p>
        </div>
      )}

      {/* Results rendering */}
      {data && (
        <div className="space-y-6">
          {/* Uncalibrated banner */}
          {data.uncalibrated && (
            <div className="px-4 py-3 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-xs text-indigo-300 flex items-center justify-between">
              <span className="leading-relaxed">
                ℹ️ <strong>System Note:</strong> Operating in <em>uncalibrated mode</em> (refusal threshold τ_ce is pending empirical calibration on dev benchmark split).
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-900/60 border border-indigo-700/50 shrink-0 ml-2">DEV BENCHMARK</span>
            </div>
          )}

          {/* State 1: NO CORPUS */}
          {data.status === 'no_corpus' && (
            <EmptyState
              title="Corpus Waiting for Human Data Drop"
              description="Vector index contains 0 documents. Ingestion pipeline is waiting for license-cleared PDFs to be placed in data/pdfs/."
              actionText="Run 'python scripts/build_index.py' after placing PDFs."
            />
          )}

          {/* State 2: NEEDS CLARIFICATION */}
          {data.status === 'needs_clarification' && (
            <div className="p-6 rounded-2xl border border-purple-900/60 bg-purple-950/30 space-y-4 shadow-lg">
              <div className="flex items-center gap-2 text-purple-200 font-semibold text-base">
                <span>⚠️</span> Combustion Boundary Conditions Required
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                {data.refusal_reason || 'Query lacks essential physical boundary conditions.'}
              </p>
              {data.missing_conditions && data.missing_conditions.length > 0 && (
                <div className="text-xs font-mono text-purple-200 bg-purple-950/70 p-3.5 rounded-xl border border-purple-900/50">
                  <div className="text-[10px] uppercase tracking-wider text-purple-400 font-bold mb-1">Required Physical Boundary Parameters:</div>
                  <strong className="text-purple-100">{data.missing_conditions.join(' · ')}</strong>
                </div>
              )}
            </div>
          )}

          {/* State 3: INSUFFICIENT / REFUSAL */}
          {data.status === 'insufficient' && (
            <RefusalCard
              reason={data.refusal_reason}
              nearestDocuments={data.nearest_documents}
            />
          )}

          {/* State 4: ANSWERED */}
          {data.status === 'answered' && (
            <div className="p-7 rounded-2xl border border-slate-800 bg-slate-900/70 shadow-2xl backdrop-blur-md space-y-6">
              {/* Top Bar with Evidence Tier & Normalized Score */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
                <div className="flex flex-wrap items-center gap-3">
                  <TierBadge tier={data.tier} rationale={data.tier_rationale} />
                  {topRelevanceScore > 0 && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-950/50 border border-blue-800/40 text-xs font-mono text-blue-300">
                      <span>Normalized Relevance:</span>
                      <strong className="text-blue-100 font-bold">{topRelevanceScore.toFixed(3)}</strong>
                    </div>
                  )}
                  {data.generation_mode && (
                    <span className="text-xs font-mono text-slate-400 bg-slate-800/70 px-2.5 py-1 rounded-md border border-slate-700">
                      Mode: <strong className="text-slate-200">{data.generation_mode === 'llm' ? 'LLM Synthesis' : 'Deterministic Grounded'}</strong>
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-300 bg-emerald-950/50 px-3 py-1.5 rounded-lg border border-emerald-800/50">
                  <span>✓</span>
                  <span>Sentence Citations Linked & Number-Checked</span>
                </div>
              </div>

              {/* Sentences with Citations */}
              <div className="space-y-4">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
                  Synthesized Scientific Findings:
                </div>
                {data.answer_sentences.map((sent, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/50 space-y-3 transition-colors hover:border-slate-700/80">
                    <div className="flex items-start gap-3">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 shrink-0 mt-0.5">
                        #{String(idx + 1).padStart(2, '0')}
                      </span>
                      <p className="text-slate-100 text-sm sm:text-base leading-relaxed flex-1">
                        {sent.text}
                      </p>
                    </div>
                    <div className="pl-9">
                      <CitationList citations={sent.citations} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Multi-Factor Ranking Breakdown Expander */}
              <RankBreakdown items={data.rank_breakdown} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
