import { useState } from 'react';
import { Link } from 'react-router-dom';

const steps = [
  { label: 'Find the unexpected', title: 'A visible flame can go out while combustion continues.', body: 'Choose Detection & extinction in the explorer. Read the FLEX observation and open its NASA source. Notice the distinction between the observation and our interpretation.', href: '/?focus=detection', action: 'Explore FLEX evidence' },
  { label: 'Challenge the transfer', title: 'Would that result apply to a lunar habitat?', body: 'In Applicability, select Lunar surface and Solid materials. Inspect the gravity mismatch and the FLEX fuel-class mismatch. Unknown atmosphere conditions remain unknown.', href: '/applicability?mission=lunar', action: 'Inspect the lunar evidence gap' },
  { label: 'Make the next question precise', title: 'An evidence gap should lead to a better research request.', body: 'Enter a research atmosphere in Applicability. Export the assessment, or pass its question to the literature workspace. User inputs never turn into verified measurements.', href: '/applicability', action: 'Build a research question' },
  { label: 'Keep the audit trail', title: 'Carry the source and the limitation with the insight.', body: 'Add findings to your mission brief and download it. The export preserves observations, interpretations, source links and limitations. Your selected findings stay saved in this browser.', href: '/', action: 'Build an evidence brief' },
];
export function DemoGuide() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);
  const current = steps[step];
  return <section className={`demo-guide ${open ? 'is-open' : ''}`} aria-label="Guided product walkthrough">
    <button className="demo-toggle" aria-expanded={open} onClick={() => setOpen(!open)}><span><span className="demo-play" aria-hidden="true">▷</span> The three-minute mission walkthrough</span><span>{open ? 'Close −' : 'Start tour ↗'}</span></button>
    {open && <div className="demo-content"><div className="demo-steps">{steps.map((s, i) => <button aria-pressed={step === i} key={s.label} onClick={() => setStep(i)}><small>0{i + 1}</small>{s.label}</button>)}</div><div className="demo-detail" aria-live="polite"><h2>{current.title}</h2><p>{current.body}</p><Link to={current.href}>{current.action} ↗</Link><div className="demo-pagination"><button disabled={step === 0} onClick={() => setStep(step - 1)}>← Previous</button><span>{step + 1} / {steps.length}</span><button disabled={step === steps.length - 1} onClick={() => setStep(step + 1)}>Next →</button></div></div></div>}
  </section>;
}
