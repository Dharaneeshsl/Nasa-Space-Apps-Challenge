import { describe, it, expect } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MissionControl } from '../pages/MissionControl';
import { buildBrief, findings, rankFindings } from '../lib/mission';

describe('mission evidence explorer', () => {
  it('prioritizes relevant research without inventing evidence for an unmatched search', () => {
    expect(rankFindings('detection', '')[0].id).toBe('flex');
    expect(rankFindings('atmosphere', '')[0].id).toBe('saffire');
    expect(rankFindings('all', 'regolith')).toEqual([]);
    expect(rankFindings('all', 'FLEX').map(f => f.id)).toEqual(['flex']);
  });
  it('exports sources and limitations for only the selected evidence', () => {
    const brief = buildBrief('lunar', 'detection', [findings[2]]);
    expect(brief).toContain(findings[2].source);
    expect(brief).toContain(findings[2].gap);
    expect(brief).toContain('partial-gravity applicability remains unvalidated');
    expect(brief).toContain('Not an AI-generated literature review');
    expect(brief).not.toContain(findings[0].source);
  });
  it('supports mission selection, evidence selection and an honest empty state', () => {
    render(<MemoryRouter><MissionControl /></MemoryRouter>);
    const download = screen.getByRole('button', { name: /Download research brief/ });
    expect(download).toBeDisabled();
    fireEvent.click(screen.getAllByRole('button', { name: /Add to brief/ })[0]);
    expect(download).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: /Lunar surface/ }));
    expect(screen.getByText(/Lunar partial-gravity applicability remains unvalidated/)).toBeInTheDocument();
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'regolith' } });
    expect(screen.getByText('No matching evidence in this collection.')).toBeInTheDocument();
    expect(download).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: /Remove .* from brief/ }));
    expect(download).toBeDisabled();
  });
});
