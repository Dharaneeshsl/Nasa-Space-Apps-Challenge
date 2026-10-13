import React from 'react';

interface VerifiedValueProps {
  value: any;
  suffix?: string;
}

export const VerifiedValue: React.FC<VerifiedValueProps> = ({ value, suffix }) => {
  if (value === null || value === undefined || value === '') {
    return (
      <span data-testid="null-value" className="text-amber-500/80 italic font-normal">
        not verified
      </span>
    );
  }
  return (
    <strong data-testid="verified-value" className="text-slate-100 font-semibold">
      {String(value)}{suffix ? ` ${suffix}` : ''}
    </strong>
  );
};
