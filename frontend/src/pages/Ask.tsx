import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { askQuestion } from '../lib/api';
import { AskResponse } from '../lib/types';
import { TierBadge } from '../components/TierBadge';
import { RankBreakdown } from '../components/RankBreakdown';
import { CitationList } from '../components/CitationList';
import { RefusalCard } from '../components/RefusalCard';
import { EmptyState } from '../components/EmptyState';

const SAMPLE_QUERIES = [
  "What is the droplet burning rate constant of n-heptane in microgravity under quiescent flow at 101 kPa?",
  "How does low-speed forced convection affect flame spread over PMMA in microgravity?",
  "What is the radiative extinction limit of spherical droplet flames?",
  "What are the flammability limits of regolith on lunar surface?",
];

export const Ask: React.FC = () => {
  const [query, setQuery] = useState('');

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
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          <span>🔬</span> Ask CombustionLens
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Grounded Q&A strictly synthesized from peer-reviewed NASA microgravity combustion papers with page-level citations.
        </p>
      </div>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <label htmlFor="research-query-input" className="block text-xs font-mono text-slate-400">
          Enter Research Question (max 500 characters):
        </label>
        <div className="flex gap-2">
          <input
            id="research-query-input"
            type="text"
            maxLength={500}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What is the burning rate of n-heptane droplets under microgravity?"
            className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-sans text-sm"
          />
          <button
            type="submit"
            disabled={mutation.isPending || !query.trim()}
            className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-sm transition-colors shadow-lg shadow-blue-900/30 shrink-0"
          >
            {mutation.isPending ? 'Searching...' : 'Explore Evidence'}
          </button>
        </div>

        {/* Sample query pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-slate-500">Sample Queries:</span>
          {SAMPLE_QUERIES.map((sq, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(sq);
                mutation.mutate(sq);
              }}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors truncate max-w-xs"
            >
              {sq}
            </button>
          ))}
        </div>
      </form>

      {/* Loading state */}
      {mutation.isPending && (
        <div className="p-8 text-center border border-slate-800 rounded-xl bg-slate-900/40 text-slate-400 font-mono text-sm animate-pulse">
          Searching vector embeddings, calculating cross-encoder rerank logits, and verifying citation numbers...
        </div>
      )}

      {/* Error state */}
      {mutation.isError && (
        <div className="p-4 rounded-xl border border-red-900/40 bg-red-950/20 text-red-300 text-sm">
          Failed to process query: {mutation.error.message}
        </div>
      )}

      {/* Results rendering */}
      {data && (
        <div className="space-y-6">
          {/* Uncalibrated banner */}
          {data.uncalibrated && (
            <div className="px-4 py-2 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-300 flex items-center justify-between">
              <span>
                ℹ️ <strong>System Note:</strong> Operating in <em>uncalibrated mode</em> (refusal threshold τ_ce is pending empirical calibration on dev benchmark split).
              </span>
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
            <div className="p-6 rounded-xl border border-purple-900/60 bg-purple-950/20 space-y-3">
              <div className="flex items-center gap-2 text-purple-300 font-semibold text-base">
                <span>⚠️</span> Combustion Boundary Conditions Required
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                {data.refusal_reason || 'Query lacks essential physical boundary conditions.'}
              </p>
              {data.missing_conditions && data.missing_conditions.length > 0 && (
                <div className="text-xs font-mono text-purple-300 bg-purple-950/50 p-3 rounded border border-purple-900/40">
                  Missing parameters to specify:{' '}
                  <strong>{data.missing_conditions.join(', ')}</strong>
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
            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-6">
              {/* Top Bar with Evidence Tier & Normalized Score */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-3">
                  <TierBadge tier={data.tier} rationale={data.tier_rationale} />
                  {topRelevanceScore > 0 && (
                    <span className="text-xs font-mono text-blue-300 bg-blue-950/40 px-2.5 py-1 rounded border border-blue-800/40">
                      Top Normalized Relevance: {(topRelevanceScore * 100).toFixed(1)}%
                    </span>
                  )}
                  {data.generation_mode && (
                    <span className="text-xs font-mono text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700">
                      Mode: {data.generation_mode === 'llm' ? 'LLM Synthesis' : 'Deterministic Grounded'}
                    </span>
                  )}
                </div>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded border border-emerald-800/40">
                  Sentence Citations Linked & Number-Checked
                </span>
              </div>

              {/* Sentences with Citations */}
              <div className="space-y-4">
                {data.answer_sentences.map((sent, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <p className="text-slate-100 text-sm sm:text-base leading-relaxed">
                      {sent.text}
                    </p>
                    <CitationList citations={sent.citations} />
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
