import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getSystemStatus } from '../lib/api';

export const Footer: React.FC = () => {
  const { data: status } = useQuery({
    queryKey: ['system-status'],
    queryFn: getSystemStatus,
    refetchInterval: 30000,
  });

  return (
    <footer
      data-testid="global-footer"
      className="mt-16 border-t border-slate-800/80 bg-slate-950/80 backdrop-blur py-8 text-xs text-slate-400"
    >
      <div className="max-w-6xl mx-auto px-4 space-y-4">
        {/* Mandatory Safety Disclaimer */}
        <div className="p-3.5 rounded-lg border border-red-900/40 bg-red-950/20 text-red-200/90 font-medium leading-relaxed">
          <strong>Mandatory Notice:</strong>{' '}
          {status?.disclaimer ||
            'Generated from published NASA research for informational/research purposes. Not validated for operational flight or terrestrial fire safety decisions.'}
        </div>

        {/* Global Metadata & Live Stats */}
        <div className="flex flex-wrap items-center justify-between gap-4 font-mono text-slate-400">
          <div className="flex items-center gap-3">
            <span>
              Corpus: <strong className="text-slate-200">{status?.corpus_size ?? 0} papers</strong>
            </span>
            <span>•</span>
            <span>
              Verified Rows:{' '}
              <strong className="text-slate-200">{status?.verified_rows ?? 0}</strong>
            </span>
            <span>•</span>
            <span className="text-amber-400">
              Mode: {status?.tau_ce_mode || 'uncalibrated'}
            </span>
            <span>•</span>
            <span>
              Updated: <strong className="text-slate-300">{status?.last_data_update || 'not verified'}</strong>
            </span>
          </div>

          <div className="text-slate-400">
            CombustionLens • NASA Space Apps Challenge 2026
          </div>
        </div>
      </div>
    </footer>
  );
};
