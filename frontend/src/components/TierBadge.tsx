import React from 'react';

interface TierBadgeProps {
  tier?: string;
  rationale?: string;
}

export const TierBadge: React.FC<TierBadgeProps> = ({ tier = 'INSUFFICIENT', rationale }) => {
  const t = tier.toUpperCase();

  // Tier colors ALWAYS paired with explicit text labels
  const config: Record<string, { bg: string; text: string; border: string; label: string }> = {
    STRONG: {
      bg: 'bg-emerald-950/70',
      text: 'text-emerald-300',
      border: 'border-emerald-600/50',
      label: 'Strong Evidence (2+ Groups)',
    },
    MODERATE: {
      bg: 'bg-blue-950/70',
      text: 'text-blue-300',
      border: 'border-blue-600/50',
      label: 'Moderate Evidence (1 Group Peer-Reviewed)',
    },
    WEAK: {
      bg: 'bg-amber-950/70',
      text: 'text-amber-300',
      border: 'border-amber-600/50',
      label: 'Weak / Preliminary Evidence',
    },
    CONFLICTING: {
      bg: 'bg-rose-950/70',
      text: 'text-rose-300',
      border: 'border-rose-600/50',
      label: 'Conflicting / Disputed Findings',
    },
    INSUFFICIENT: {
      bg: 'bg-slate-900',
      text: 'text-slate-400',
      border: 'border-slate-700',
      label: 'Insufficient Evidence',
    },
  };

  const current = config[t] || config.INSUFFICIENT;

  return (
    <div className="inline-flex flex-col gap-1">
      <span
        data-testid="tier-badge"
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide border ${current.bg} ${current.text} ${current.border}`}
      >
        <span className="w-2 h-2 rounded-full bg-current opacity-80" />
        {current.label}
      </span>
      {rationale && (
        <span className="text-xs text-slate-400 italic max-w-lg">
          {rationale}
        </span>
      )}
    </div>
  );
};
