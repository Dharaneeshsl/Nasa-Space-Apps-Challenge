import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { RankBreakdown } from '../components/RankBreakdown';
import { RankItem } from '../lib/types';

describe('RankBreakdown Component', () => {
  const SYNTHETIC_ITEMS: RankItem[] = [
    {
      doc_id: 'SYNTH_TEST_DOC',
      raw_logit: 2.5,
      s_rel: 1.0,
      s_corrob: 0.67,
      s_source: 1.0,
      weights: { w_rel: 0.6, w_corrob: 0.25, w_source: 0.15 },
      rank_score: 0.9175,
      distinct_groups_count: 2,
      has_contradiction: false,
      arithmetic_formula: '0.6*1.0 + 0.25*0.67 + 0.15*1.0 = 0.9175',
      source_type_caveat: 'S_source is an environmental representativeness prior, not a truth rating.',
    },
  ];

  it('toggles ranking arithmetic accordion and displays formula', () => {
    render(<RankBreakdown items={SYNTHETIC_ITEMS} />);
    const toggleBtn = screen.getByText(/Transparent Multi-Factor Ranking Inspection/i);
    fireEvent.click(toggleBtn);

    expect(screen.getByText(/0.6\*1.0 \+ 0.25\*0.67 \+ 0.15\*1.0 = 0.9175/i)).toBeInTheDocument();
    expect(screen.getByText(/Composite Score: 0.9175/i)).toBeInTheDocument();
  });
});
