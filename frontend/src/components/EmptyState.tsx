import React from 'react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available Yet',
  description = 'Data files are currently empty slots. As soon as NASA dataset files are populated, they will automatically appear here.',
  actionText,
}) => {
  return (
    <div
      data-testid="empty-state"
      className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30 text-slate-400 space-y-3"
    >
      <div className="text-4xl">🛰️</div>
      <h3 className="text-base font-semibold text-slate-200">{title}</h3>
      <p className="text-sm max-w-md mx-auto leading-relaxed">{description}</p>
      {actionText && (
        <span className="inline-block mt-2 text-xs font-mono text-blue-400 bg-blue-950/40 px-3 py-1 rounded border border-blue-900/50">
          {actionText}
        </span>
      )}
    </div>
  );
};
