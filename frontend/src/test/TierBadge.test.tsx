import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { TierBadge } from '../components/TierBadge';

describe('TierBadge Component', () => {
  it('renders Strong Evidence with explicit text label', () => {
    render(<TierBadge tier="STRONG" rationale="Corroborated across 2 groups." />);
    expect(screen.getByText(/Strong Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Corroborated across 2 groups/i)).toBeInTheDocument();
  });

  it('renders Moderate Evidence label', () => {
    render(<TierBadge tier="MODERATE" />);
    expect(screen.getByText(/Moderate Evidence/i)).toBeInTheDocument();
  });

  it('renders Insufficient Evidence label by default', () => {
    render(<TierBadge tier="INSUFFICIENT" />);
    expect(screen.getByText(/Insufficient Evidence/i)).toBeInTheDocument();
  });
});
