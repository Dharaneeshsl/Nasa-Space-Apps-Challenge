import { findings, Mission, missions } from './mission';

export type FuelClass = 'solid' | 'droplet' | 'unspecified';
export interface Scenario { mission: Mission; fuel: FuelClass; oxygen: string; pressure: string; flow: string }
export interface BoundaryCheck { condition: string; status: 'aligned' | 'mismatch' | 'unknown'; explanation: string }
export const defaultScenario: Scenario = { mission: 'orbital', fuel: 'solid', oxygen: '', pressure: '', flow: '' };
const fuelByCampaign: Record<string, Exclude<FuelClass, 'unspecified'>> = { bass: 'solid', flex: 'droplet', sofie: 'solid', saffire: 'solid' };
export function validateScenario(s: Scenario): string[] {
  const errors: string[] = [];
  if (s.oxygen.trim() && (!Number.isFinite(Number(s.oxygen)) || Number(s.oxygen) <= 0 || Number(s.oxygen) > 100)) errors.push('Oxygen must be greater than 0 and no more than 100 percent by volume.');
  if (s.pressure.trim() && (!Number.isFinite(Number(s.pressure)) || Number(s.pressure) <= 0)) errors.push('Pressure must be a positive number in kPa.');
  return errors;
}
export function assessApplicability(s: Scenario, id: string): BoundaryCheck[] {
  if (!findings.some(f => f.id === id)) throw new Error('Unknown evidence record');
  return [
    { condition: 'Gravity', status: s.mission === 'lunar' ? 'mismatch' : 'aligned', explanation: s.mission === 'lunar' ? 'Microgravity source; lunar partial gravity is not represented.' : 'Same broad gravity regime. This is not a complete experimental match.' },
    { condition: 'Fuel class', status: s.fuel === 'unspecified' ? 'unknown' : s.fuel === fuelByCampaign[id] ? 'aligned' : 'mismatch', explanation: s.fuel === 'unspecified' ? 'Choose the fuel class to assess this boundary.' : `Source class: ${fuelByCampaign[id]}. Exact material and sample geometry still need verification.` },
    ...(['Oxygen', 'Pressure', 'Ventilation', 'Geometry / scale'] as const).map(condition => ({ condition, status: 'unknown' as const, explanation: 'No run-level matching data in this curated summary. A user-entered value is a research target, not verified evidence.' })),
  ];
}
export function researchQuestion(s: Scenario): string {
  const fuel = s.fuel === 'droplet' ? 'liquid droplets' : s.fuel === 'solid' ? 'solid materials' : 'an unspecified fuel';
  const atmosphere = [s.oxygen.trim() ? `${s.oxygen}% oxygen by volume` : 'oxygen unspecified', s.pressure.trim() ? `${s.pressure} kPa` : 'pressure unspecified', s.flow.trim() ? `${s.flow.trim()} flow` : 'flow unspecified'].join(', ');
  return `What evidence and transferability gaps apply to ${fuel} in ${missions[s.mission].name.toLowerCase()} (${s.mission === 'lunar' ? 'partial gravity' : 'microgravity'}), at ${atmosphere}?`;
}
export function exportAssessment(s: Scenario): string {
  if (validateScenario(s).length) throw new Error('Correct scenario inputs before exporting');
  return ['# CombustionLens | Applicability assessment', `Generated: ${new Date().toISOString()}`, '',
    'User-defined research scenario, not a recommended cabin configuration. No safe/unsafe classification is produced.',
    'Method: deterministic gravity and fuel-class boundary checks against curated NASA campaign summaries. Aligned means broad category alignment only; unknown values never count as matches.', '',
    '## Research question', researchQuestion(s), '', ...findings.flatMap(f => [`## ${f.campaign}`, ...assessApplicability(s, f.id).map(c => `- ${c.condition}: ${c.status.toUpperCase()} — ${c.explanation}`), `Source: ${f.source}`, '']),
    '## Required next evidence', 'Obtain run-level material, geometry, oxygen, pressure, flow, gravity and uncertainty records. Use independently verified records for numerical comparisons.',
  ].join('\n');
}
