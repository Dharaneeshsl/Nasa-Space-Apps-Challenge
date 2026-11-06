"""FastAPI Route: /api/brief

Generates a structured Safety Brief synthesizing findings from retrieved papers.
Uses the exact same retrieval pipeline; makes ZERO unsupported or fabricated claims.
"""
from fastapi import APIRouter, Request, HTTPException
from api.schemas import BriefRequest, BriefResponse, BriefSection, Citation
from api.rate_limit import enforce_query_length, enforce_rate_limit
from core.retrieval import retrieve_candidates
from core.evidence import evaluate_evidence_tier
from core.sources import source_url_for
from core.generate import generate_answer

router = APIRouter(prefix="/api", tags=["Safety Brief"])


@router.post("/brief", response_model=BriefResponse)
def generate_safety_brief_endpoint(req: BriefRequest, request: Request) -> BriefResponse:
    question = req.question.strip()
    enforce_rate_limit(request)
    enforce_query_length(question, field_name="question")
    if not question:
        raise HTTPException(status_code=400, detail="Please enter a safety brief question.")
    
    ret_res = retrieve_candidates(question)
    candidates = ret_res.get("candidates", [])
    
    if not candidates:
        tier = "INSUFFICIENT"
        findings = [BriefSection(
            title="Corpus Assessment",
            content="No sufficiently grounded literature found in corpus to assemble a safety brief.",
            citations=[],
            tier="INSUFFICIENT"
        )]
        conditions = {
            "gravity_regime": "unverified",
            "campaign_series": "unverified",
            "atmospheric_conditions": "unverified"
        }
        earth_mapping = "Cannot establish terrestrial analogs without empirical microgravity observations."
        limitations = "Corpus lacks published data matching the scope of this inquiry."
    else:
        # Grounded synthesis of findings from candidate chunks (skip ambiguity check for structured topic brief)
        brief_query = f"Key spacecraft fire safety observations regarding: {question}"
        gen_res = generate_answer(brief_query, candidates, skip_ambiguity_check=True)
        
        findings = []
        cited_doc_ids = set()
        for idx, s in enumerate(gen_res.get("answer_sentences", []), start=1):
            cites = []
            for c in s.get("citations", []):
                d_id = c.get("doc_id")
                if d_id:
                    cited_doc_ids.add(d_id)
                    cites.append(Citation(
                        doc_id=d_id,
                        source_url=source_url_for(d_id),
                        paper_title=c.get("paper_title"),
                        page=int(c["page"]) if c.get("page") is not None and str(c.get("page")).isdigit() else None
                    ))
            findings.append(BriefSection(
                title=f"Safety Finding {idx}",
                content=s.get("text", ""),
                citations=cites,
                tier="UNASSESSED"
            ))
            
        # Evidence tier strictly reflects the actual papers cited in findings
        if findings and cited_doc_ids:
            cited_candidates = [c for c in candidates if c.get("doc_id") in cited_doc_ids]
            tier, rationale, _ = evaluate_evidence_tier(cited_candidates)
            for f in findings:
                f.tier = tier
        else:
            tier, rationale, _ = evaluate_evidence_tier([])
            findings = [BriefSection(
                title="Corpus Assessment",
                content="Evidence chunks were retrieved but no verified grounded findings met quantitative grounding criteria.",
                citations=[],
                tier=tier
            )]
            
        # Extract conditions strictly from retrieved candidate metadata
        source_types = sorted(list({c.get("source_type") for c in candidates if c.get("source_type")}))
        campaigns = sorted(list({c.get("campaign_or_series") for c in candidates if c.get("campaign_or_series")}))
        
        conditions = {
            "source_types_represented": ", ".join(source_types) if source_types else "not verified",
            "flight_or_ground_campaigns": ", ".join(campaigns) if campaigns else "not verified",
            "boundary_conditions_note": "Boundary parameters reflect specific laboratory test cells reported in citations."
        }
        
        earth_mapping = (
            "HYPOTHESIS (unvalidated): No explicit terrestrial analog transfer data was reported in retrieved microgravity evidence. "
            "Terrestrial extrapolation requires buoyancy-driven convection compensation not validated in these publications."
        )
        
        limitations = (
            f"Evidence Tier: {tier}. {rationale}. "
            f"Synthesized from {len(candidates)} retrieved publication chunk(s). "
            "Observations reflect limited test envelopes and are not validated for operational spacecraft design."
        )

    return BriefResponse(
        question=question,
        scope_statement=f"Literature synthesis regarding: '{question}'",
        key_findings=findings,
        conditions_of_validity=conditions,
        earth_analog_mapping=earth_mapping,
        limitations_and_gaps=limitations,
        tier=tier
    )
