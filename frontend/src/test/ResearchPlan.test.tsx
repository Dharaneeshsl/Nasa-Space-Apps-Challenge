import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ResearchPlan } from '../components/ResearchPlan';
import { defaultScenario } from '../lib/applicability';

describe('research plan', () => {
  it('updates transfer barriers when a source or mission changes', () => {
    const { rerender } = render(<ResearchPlan scenario={defaultScenario} />);
    expect(screen.getByText('2 broad alignments')).toBeInTheDocument();
    expect(screen.getByText('4 unknowns')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Inspect a campaign'), { target: { value: 'flex' } });
    expect(screen.getByText(/target fuel class/)).toBeInTheDocument();
    rerender(<ResearchPlan scenario={{ ...defaultScenario, mission: 'lunar' }} />);
    expect(screen.getByText('2 mismatches')).toBeInTheDocument();
    expect(screen.getByText(/target gravity and fuel class/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Start with the NASA source/ })).toHaveAttribute('href', 'https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/');
  });
});
