import React from 'react';
import { CompareCheck } from '../lib/types';

interface GuardrailCardProps {
  state: 'PASS' | 'PASS_WITH_WARNINGS' | 'GUARDRAIL_FAILURE';
  checks: CompareCheck[];
}

export const GuardrailCard: React.FC<GuardrailCardProps> = ({ state, checks }) => {
  const stateConfig = {
    PASS: {
      border: 'border-emerald-600/50',
      bg: 'bg-emerald-950/20',
      titleColor: 'text-emerald-400',
      icon: '✅',
      headline: 'Scientific Comparability Verified: Direct Comparison Permitted',
    },
    PASS_WITH_WARNINGS: {
      border: 'border-amber-600/50',
      bg: 'bg-amber-950/20',
      titleColor: 'text-amber-400',
      icon: '⚠️',
      headline: 'Pass with Atmospheric/Parameter Warnings (Values for Reference Only)',
    },
    GUARDRAIL_FAILURE: {
      border: 'border-rose-600/60',
      bg: 'bg-rose-950/30',
      titleColor: 'text-rose-400',
      icon: '🚫',
      headline: 'Scientific Guardrail Failure: Direct Comparison Incompatible',
    },
  };

  const current = stateConfig[state] || stateConfig.GUARDRAIL_FAILURE;

  return (
    <div
      data-testid="guardrail-card"
      className={`p-6 rounded-xl border ${current.border} ${current.bg} text-slate-200 space-y-4`}
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl">{current.icon}</span>
        <div>
          <h3 className={`text-base font-bold ${current.titleColor}`}>
            {current.headline}
          </h3>
          <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
            Status: {state.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      <div className="pt-2 divide-y divide-slate-800">
        {checks.map((check, idx) => {
          const badgeStyles = {
            pass: 'bg-emerald-950 text-emerald-400 border-emerald-800',
            warning: 'bg-amber-950 text-amber-300 border-amber-800',
            failure: 'bg-rose-950 text-rose-400 border-rose-800',
          }[check.result] || 'bg-slate-900 text-slate-400 border-slate-700';

          return (
            <div key={idx} className="py-3 first:pt-0 last:pb-0 text-sm space-y-1">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-100">{check.name}</span>
                <span className={`text-xs px-2.5 py-0.5 rounded border font-mono uppercase font-bold ${badgeStyles}`}>
                  {check.result}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {check.reason}
              </p>
              {check.values && (
                <div className="text-xs font-mono text-slate-400 pt-1 flex gap-4">
                  {Object.entries(check.values).map(([k, v]) => (
                    <span key={k}>
                      {k}: <strong className="text-slate-200">{String(v)}</strong>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
