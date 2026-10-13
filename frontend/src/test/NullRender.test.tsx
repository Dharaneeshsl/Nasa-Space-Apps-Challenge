import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { VerifiedValue } from '../components/VerifiedValue';

describe('Hard Rule #2: Null on Ambiguity Rendering via VerifiedValue Component', () => {
  it('renders "not verified" when value is null', () => {
    render(<VerifiedValue value={null} />);
    const elem = screen.getByTestId('null-value');
    expect(elem).toHaveTextContent('not verified');
  });

  it('renders "not verified" when value is undefined', () => {
    render(<VerifiedValue value={undefined} />);
    const elem = screen.getByTestId('null-value');
    expect(elem).toHaveTextContent('not verified');
  });

  it('renders "not verified" when value is an empty string', () => {
    render(<VerifiedValue value="" />);
    const elem = screen.getByTestId('null-value');
    expect(elem).toHaveTextContent('not verified');
  });

  it('renders verified value and suffix when present', () => {
    render(<VerifiedValue value={101.3} suffix="kPa" />);
    const elem = screen.getByTestId('verified-value');
    expect(elem).toHaveTextContent('101.3 kPa');
  });
});

