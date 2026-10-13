import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { GuardrailCard } from '../components/GuardrailCard';
import { CompareCheck } from '../lib/types';

describe('GuardrailCard Component', () => {
  const SYNTHETIC_CHECKS_FAILURE: CompareCheck[] = [
    {
      name: 'Fuel Class & Geometry',
      result: 'failure',
      reason: 'Incompatible combustion regimes: droplet vs cast_solid.',
      values: { exp_a: 'droplet', exp_b: 'cast_solid' },
    },
  ];

  it('renders explicit GUARDRAIL FAILURE status card', () => {
    render(<GuardrailCard state="GUARDRAIL_FAILURE" checks={SYNTHETIC_CHECKS_FAILURE} />);
    expect(
      screen.getByText(/Scientific Guardrail Failure: Direct Comparison Incompatible/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Incompatible combustion regimes: droplet vs cast_solid/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText(/failure/i).length).toBeGreaterThan(0);
  });
});
