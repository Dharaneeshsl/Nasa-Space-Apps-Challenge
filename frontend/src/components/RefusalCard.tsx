import React from 'react';

interface RefusalCardProps {
  reason?: string;
  nearestDocuments?: Array<Record<string, any>>;
  title?: string;
}

export const RefusalCard: React.FC<RefusalCardProps> = ({
  reason = 'The query could not be substantiated with sufficient empirical evidence from the indexed NASA research papers.',
  nearestDocuments = [],
  title = 'No sufficiently relevant evidence in the corpus',
}) => {
  const isNumberFilter = reason.toLowerCase().includes('number') || reason.toLowerCase().includes('numerical');
  const displayTitle = title !== 'No sufficiently relevant evidence in the corpus'
    ? title
    : (isNumberFilter ? 'Generated text suppressed: unverified numerical values detected' : title);
  const candidatesHeading = isNumberFilter
    ? 'Retrieved Document Candidates (Numerical Assertions Unverified in Text):'
    : 'Nearest Document Candidates (Below Acceptance Threshold):';

  return (
    <div
      data-testid="refusal-card"
      className="p-6 rounded-xl border border-amber-900/50 bg-amber-950/20 text-slate-200 space-y-4"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <h3 className="text-base font-semibold text-amber-300">
            {displayTitle}
          </h3>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">
            {reason}
          </p>
          <div className="mt-2 text-xs font-mono text-amber-400/90 bg-amber-950/40 px-2.5 py-1 rounded border border-amber-800/40 inline-block">
            Scientific Guardrail Active: Zero ungrounded text generated.
          </div>
        </div>
      </div>

      {nearestDocuments && nearestDocuments.length > 0 && (
        <div className="pt-4 border-t border-amber-900/40">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            {candidatesHeading}
          </h4>
          <div className="space-y-2">
            {nearestDocuments.slice(0, 3).map((doc, idx) => (
              <div
                key={idx}
                className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex justify-between items-center text-xs font-mono"
              >
                <div className="truncate max-w-md">
                  <span className="text-slate-200 font-medium">
                    {doc.title || doc.doc_id || 'NASA Document'}
                  </span>
                  <span className="text-slate-500 ml-2">
                    {doc.page_number ? `(Page ${doc.page_number})` : '(page unverified)'}
                  </span>
                </div>
                <div className="text-amber-400 font-bold shrink-0 ml-4">
                  Logit: {doc.raw_logit !== undefined ? doc.raw_logit.toFixed(3) : 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
