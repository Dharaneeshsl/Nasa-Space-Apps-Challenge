export type Mission = 'orbital' | 'lunar' | 'transit';
export type Focus = 'all' | 'materials' | 'detection' | 'atmosphere';
export interface Finding {
  id: string; campaign: string; title: string; observation: string; implication: string;
  gap: string; focus: Exclude<Focus, 'all'>; source: string; sourceTitle: string;
  kind: 'Published observation' | 'Investigation scope';
}
export const missions: Record<Mission, { name: string; context: string; gap: string }> = {
  orbital: { name: 'Orbital habitat', context: 'Microgravity · crewed cabin', gap: 'Match the actual material, ventilation, pressure and oxygen conditions before transferring a finding.' },
  lunar: { name: 'Lunar surface', context: 'Partial gravity · exploration habitat', gap: 'These sources describe microgravity research. Lunar partial-gravity applicability remains unvalidated in this collection.' },
  transit: { name: 'Mars transit', context: 'Microgravity · long-duration habitat', gap: 'Microgravity is relevant, but mission-specific cabin scale, materials and atmosphere remain unverified.' },
};
// Curated qualitative summaries, not numerical experiment rows or peer-reviewed claims.
// Source pages checked 2026-11-06. Interpretation is explicitly separate from observation.
export const findings: Finding[] = [
  { id: 'saffire', campaign: 'SAFFIRE VI', title: 'Atmosphere changes the experiment.', focus: 'atmosphere', kind: 'Published observation',
    observation: 'NASA reports that Saffire VI tested fires at higher oxygen concentration and lower pressure, extending spacecraft-scale combustion research.',
    implication: 'Review oxygen concentration and total pressure together when selecting relevant fire research.',
    gap: 'This overview does not provide a validated safe operating envelope for a proposed cabin.',
    source: 'https://www.nasa.gov/centers-and-facilities/glenn/flame-burns-out-on-nasas-long-running-spacecraft-fire-experiment/', sourceTitle: 'NASA · Flame Burns Out on NASA’s Long-Running Spacecraft Fire Experiment' },
  { id: 'bass', campaign: 'BASS', title: 'Airflow belongs in the safety question.', focus: 'materials', kind: 'Published observation',
    observation: 'NASA describes how sufficient ventilation can allow materials to burn as well in microgravity as in normal gravity.',
    implication: 'Include ventilation and sample geometry in material comparisons; gravity alone is not a sufficient match.',
    gap: 'A campaign-level summary cannot establish a flame-spread rate for a particular material or airflow.',
    source: 'https://www.nasa.gov/missions/station/iss-research/youre-hot-then-youre-cold/', sourceTitle: 'NASA · You’re Hot Then You’re Cold' },
  { id: 'flex', campaign: 'FLEX', title: 'A vanished flame is not the whole story.', focus: 'detection', kind: 'Published observation',
    observation: 'FLEX revealed cool-flame combustion continuing under some conditions after the visible droplet flame extinguished.',
    implication: 'Investigate whether detection concepts capture combustion beyond visible flame signals.',
    gap: 'Droplet findings do not establish that the same behavior occurs in all solid spacecraft materials.',
    source: 'https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/', sourceTitle: 'NASA · Studying Combustion and Fire Safety' },
  { id: 'sofie', campaign: 'SoFIE-GEL', title: 'Material temperature is part of the boundary.', focus: 'materials', kind: 'Investigation scope',
    observation: 'SoFIE-GEL investigates growth and extinction over a heated PMMA sphere while varying flow, oxygen and pressure.',
    implication: 'Track heating history and fuel geometry alongside the cabin atmosphere in an evidence request.',
    gap: 'An investigation description identifies variables; it does not by itself supply measured extinction limits.',
    source: 'https://science.nasa.gov/biological-physical/investigations/sofie-gel/', sourceTitle: 'NASA Science · SoFIE-GEL' },
];
export function rankFindings(focus: Focus, query: string): Array<Finding & { score: number; reasons: string[] }> {
  const words = [...new Set(query.toLowerCase().split(/\W+/).filter(w => w.length > 2))];
  return findings.map(f => {
    const haystack = `${f.campaign} ${f.title} ${f.observation} ${f.implication}`.toLowerCase();
    const matches = words.filter(w => haystack.includes(w));
    const focusMatch = focus !== 'all' && focus === f.focus;
    const observed = f.kind === 'Published observation';
    return { ...f, score: (focusMatch ? 4 : 0) + Math.min(matches.length, 3) + (observed ? 1 : 0),
      reasons: [focusMatch ? 'Focus match +4' : 'Focus match +0', `Text matches +${Math.min(matches.length, 3)}`, observed ? 'Reported observation +1' : 'Investigation scope +0'] };
  }).filter(f => !words.length || words.some(w => `${f.campaign} ${f.title} ${f.observation} ${f.implication}`.toLowerCase().includes(w)))
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
}
export function buildBrief(mission: Mission, focus: Focus, rows: Finding[]): string {
  return ['# CombustionLens | Mission evidence brief', `Generated: ${new Date().toISOString()}`, `Scenario: ${missions[mission].name}`, `Focus: ${focus}`, '',
    'Mode: curated NASA web summaries with deterministic ranking. Not an AI-generated literature review.',
    'Research prototype. Not flight-qualified safety guidance.', '', '## Transferability', missions[mission].gap, '',
    ...rows.flatMap(f => [`## ${f.campaign}: ${f.title}`, `Source type: NASA web summary; ${f.kind.toLowerCase()}.`, `Observation: ${f.observation}`, `Team interpretation: ${f.implication}`, `Evidence gap: ${f.gap}`, `Source: ${f.source}`, '']),
    '## Next evidence request', 'Obtain primary experimental records matching fuel, geometry, gravity, flow, oxygen, pressure and heating history. Independently verify numerical records before comparison.',
  ].join('\n');
}
