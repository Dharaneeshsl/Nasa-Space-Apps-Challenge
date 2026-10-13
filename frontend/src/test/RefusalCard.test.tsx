import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { RefusalCard } from '../components/RefusalCard';

describe('RefusalCard Component', () => {
  const SYNTHETIC_NEAREST_DOCS = [
    { title: 'Synthetic Drop Tower Paper', page_number: 5, raw_logit: -1.2 },
  ];

  it('renders standard refusal headline and why-we-refused reason', () => {
    const reasonText = 'Top relevance logit is below calibrated refusal threshold.';
    render(
      <RefusalCard
        reason={reasonText}
        nearestDocuments={SYNTHETIC_NEAREST_DOCS}
      />
    );

    expect(
      screen.getByText(/No sufficiently relevant evidence in the corpus/i)
    ).toBeInTheDocument();
    expect(screen.getByText(reasonText)).toBeInTheDocument();
    expect(screen.getByText(/Synthetic Drop Tower Paper/i)).toBeInTheDocument();
  });
});
