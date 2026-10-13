import React from 'react';
import { Citation } from '../lib/types';

interface CitationListProps {
  citations: Citation[];
}

export const CitationList: React.FC<CitationListProps> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 pt-1">
      {citations.map((c, idx) => (
        <span
          key={idx}
          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-950/70 border border-blue-800/60 text-blue-300 text-xs font-mono"
        >
          <span>📄</span>
          <span className="font-semibold truncate max-w-xs">{c.paper_title || c.doc_id}</span>
          {c.page !== undefined && c.page !== null ? (
            <span className="text-blue-400 font-bold">p.{c.page}</span>
          ) : (
            <span className="text-slate-400 italic text-[11px]">(page not verified)</span>
          )}
        </span>
      ))}
    </div>
  );
};
