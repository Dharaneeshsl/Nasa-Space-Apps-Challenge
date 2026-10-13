import React, { useState } from 'react';
import { RankItem } from '../lib/types';

interface RankBreakdownProps {
  items: RankItem[];
}

export const RankBreakdown: React.FC<RankBreakdownProps> = ({ items }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!items || items.length === 0) return null;

  return (
    <div className="mt-4 border border-slate-800 rounded-lg bg-slate-900/60 overflow-hidden text-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors"
      >
        <span className="font-medium flex items-center gap-2">
          <span>🔍</span> Transparent Multi-Factor Ranking Inspection ({items.length} Chunks Evaluated)
        </span>
        <span className="text-xs text-slate-500 font-mono">
          {isOpen ? '▲ Collapse' : '▼ Expand Arithmetic'}
        </span>
      </button>

      {isOpen && (
        <div className="p-4 border-t border-slate-800 space-y-4">
          <div className="p-3 bg-blue-950/30 border border-blue-900/40 rounded text-xs text-blue-200">
            <strong>Scoring Methodology:</strong> Rank = 0.60·s_rel + 0.25·S_corrob + 0.15·S_source.
            <div className="mt-1 text-slate-400">
              Note: <em>S_source is an environmental representativeness prior (flight vs drop tower vs lab), not a scientific truth rating.</em>
              Scores are Normalized Cross-Encoder Relevance Scores, not probabilities.
            </div>
          </div>

          <div className="divide-y divide-slate-800/80">
            {items.map((item, idx) => (
              <div key={idx} className="py-3 first:pt-0 last:pb-0 font-mono text-xs space-y-1">
                <div className="flex justify-between items-center text-slate-200 font-bold">
                  <span>Candidate #{idx + 1}: {item.doc_id || 'Unknown Doc'}</span>
                  <span className="text-emerald-400">Composite Score: {item.rank_score.toFixed(4)}</span>
                </div>
                <div className="text-slate-400">
                  Formula: {item.arithmetic_formula}
                </div>
                <div className="grid grid-cols-3 gap-2 text-slate-400 pt-1">
                  <div>s_rel (relevance): <span className="text-slate-200">{item.s_rel.toFixed(4)}</span></div>
                  <div>S_corrob ({item.distinct_groups_count} groups): <span className="text-slate-200">{item.s_corrob.toFixed(2)}</span></div>
                  <div>S_source (prior): <span className="text-slate-200">{item.s_source.toFixed(2)}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
