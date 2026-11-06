import { describe, it, expect } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Applicability } from '../pages/Applicability';
import { FlameStudy } from '../components/FlameStudy';
import { assessApplicability, defaultScenario, exportAssessment, validateScenario } from '../lib/applicability';

describe('applicability boundaries', () => {
  it('never promotes user-entered conditions into verified matches', () => {
    const rows = assessApplicability({ ...defaultScenario, oxygen: '30', pressure: '70', flow: 'forced' }, 'bass');
    expect(rows.filter(c => c.status === 'unknown')).toHaveLength(4);
    expect(rows.filter(c => c.status === 'aligned')).toHaveLength(2);
  });
  it('identifies both gravity and fuel mismatches for lunar solids versus FLEX', () => {
    const rows = assessApplicability({ ...defaultScenario, mission: 'lunar' }, 'flex');
    expect(rows.filter(c => c.status === 'mismatch').map(c => c.condition)).toEqual(['Gravity', 'Fuel class']);
    expect(() => assessApplicability(defaultScenario, 'invented-study')).toThrow();
  });
  it('rejects impossible inputs and keeps unspecified values unknown', () => {
    expect(validateScenario({ ...defaultScenario, oxygen: '101', pressure: '-1' })).toHaveLength(2);
    expect(validateScenario({ ...defaultScenario, oxygen: 'NaN', pressure: 'Infinity' })).toHaveLength(2);
    expect(validateScenario(defaultScenario)).toEqual([]);
    expect(assessApplicability({ ...defaultScenario, fuel: 'unspecified' }, 'bass')[1].status).toBe('unknown');
    expect(() => exportAssessment({ ...defaultScenario, oxygen: '101' })).toThrow();
  });
  it('exports boundaries and sources without claiming a safe cabin configuration', () => {
    const output = exportAssessment({ ...defaultScenario, mission: 'lunar' });
    expect(output).toContain('Gravity: MISMATCH');
    expect(output).toContain('Oxygen: UNKNOWN');
    expect(output).toContain('https://science.nasa.gov/');
    expect(output).toContain('not a recommended cabin configuration');
  });
  it('preserves mission context from the explorer and blocks invalid export', () => {
    render(<MemoryRouter initialEntries={['/applicability?mission=lunar']}><Applicability /></MemoryRouter>);
    expect(screen.getByLabelText('Mission')).toHaveValue('lunar');
    fireEvent.change(screen.getByLabelText('Oxygen (% by volume)'), { target: { value: '120' } });
    expect(screen.getByRole('alert')).toHaveTextContent('Oxygen');
    expect(screen.getByRole('button', { name: /Export applicability/ })).toBeDisabled();
    expect(screen.queryByRole('link', { name: /Investigate in literature/ })).not.toBeInTheDocument();
  });
  it('allows a qualitative gravity comparison without presenting simulated data', () => {
    render(<FlameStudy />);
    fireEvent.click(screen.getByRole('button', { name: 'Earth gravity' }));
    expect(screen.getByRole('img')).toHaveAccessibleName(/elongated Earth flame/);
    expect(screen.getByText(/not a simulation or experimental record/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Microgravity' }));
    expect(screen.getByRole('img')).toHaveAccessibleName(/rounded low-flow/);
  });
});
