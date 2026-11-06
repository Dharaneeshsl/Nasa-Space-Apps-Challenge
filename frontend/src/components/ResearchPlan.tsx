import { useState } from 'react';
import { findings } from '../lib/mission';
import { assessApplicability, Scenario } from '../lib/applicability';

export function ResearchPlan({ scenario }: { scenario: Scenario }) {
  const [campaign, setCampaign] = useState('bass');
  const finding = findings.find(f => f.id === campaign)!;
  const checks = assessApplicability(scenario, campaign);
  const aligned = checks.filter(c => c.status === 'aligned');
  const mismatches = checks.filter(c => c.status === 'mismatch');
  const unknown = checks.filter(c => c.status === 'unknown');
  return <section className="research-plan" aria-labelledby="plan-title">
    <div className="plan-header"><div><div className="eyebrow">TURN UNCERTAINTY INTO A RESEARCH PLAN</div><h2 id="plan-title">What would close the gap?</h2></div><label className="boundary-field">Inspect a campaign<select value={campaign} onChange={e => setCampaign(e.target.value)}>{findings.map(f => <option value={f.id} key={f.id}>{f.campaign}</option>)}</select></label></div>
    <div className="coverage-strip" aria-label="Boundary category counts">{checks.map(c => <span key={c.condition} className={`coverage-segment ${c.status}`} title={`${c.condition}: ${c.status}`} />)}</div>
    <div className="coverage-legend"><span><i className="aligned" />{aligned.length} broad alignments</span><span><i className="mismatch" />{mismatches.length} mismatches</span><span><i className="unknown" />{unknown.length} unknowns</span></div>
    <p className="plan-caption">Six categorical checks for {finding.campaign}. Counts describe evidence coverage, not confidence or safety.</p>
    <div className="plan-actions">
      <article><span className="plan-number">01 / RESOLVE</span><h3>{mismatches.length ? 'Address the transfer barriers' : 'Verify the apparent alignment'}</h3><p>{mismatches.length ? `Seek primary research matching your target ${mismatches.map(c => c.condition.toLowerCase()).join(' and ')}. The current source cannot establish transferability.` : 'Gravity and fuel category matches are only a starting point. Verify actual material, geometry and experimental conditions.'}</p></article>
      <article><span className="plan-number">02 / ACQUIRE</span><h3>Request the missing records</h3><p>Obtain run-level {unknown.map(c => c.condition.toLowerCase()).join(', ')} records, including units, uncertainty and exact source locations.</p></article>
      <article><span className="plan-number">03 / REVIEW</span><h3>Keep the claim within scope</h3><p>{finding.gap}</p><a href={finding.source} target="_blank" rel="noreferrer">Start with the NASA source ↗</a></article>
    </div>
  </section>;
}
