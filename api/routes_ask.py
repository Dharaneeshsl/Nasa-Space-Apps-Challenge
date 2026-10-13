"""FastAPI Route: /api/ask

Executes grounded Q&A over retrieved papers.
Enforces refusal gate (INSUFFICIENT returns NO generated text).
Checks ambiguity before synthesis.
"""
from fastapi import APIRouter, Request
from api.schemas import AskRequest, AskResponse, AnswerSentence, Citation, RankItem
from api.rate_limit import enforce_query_length, enforce_rate_limit
from core.retrieval import retrieve_candidates
from core.ranking import rank_candidates
from core.evidence import evaluate_evidence_tier
from core.generate import generate_answer, check_query_ambiguity

router = APIRouter(prefix="/api", tags=["Ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question_endpoint(req: AskRequest, request: Request) -> AskResponse:
    query = req.query.strip()
    enforce_rate_limit(request)
    enforce_query_length(query, field_name="query")
    if not query:
        return AskResponse(
            status="insufficient",
            refusal_reason="Empty query submitted.",
            answer_sentences=[],
            nearest_documents=[]
        )

    # 1. Check physical ambiguity first
    is_ambiguous, missing_conditions = check_query_ambiguity(query)
    if is_ambiguous:
        return AskResponse(
            status="needs_clarification",
            answer_sentences=[],
            tier="INSUFFICIENT",
            tier_rationale="Query omits essential boundary conditions.",
            rank_breakdown=[],
            normalized_relevance_scores={},
            nearest_documents=[],
            missing_conditions=missing_conditions,
            refusal_reason=(
                f"Query lacks essential physical boundary conditions: {', '.join(missing_conditions)}. "
                "Combustion behavior depends heavily on fuel, pressure, gravity level, and flow regime. "
                "Please specify these parameters for a grounded answer."
            ),
            uncalibrated=True
        )

    # 2. Two-stage retrieval & refusal gate
    ret_res = retrieve_candidates(query)
    status = ret_res["status"]
    candidates = ret_res.get("candidates", [])
    nearest = ret_res.get("nearest_documents", [])
    top_logit = ret_res.get("top_logit")
    tau_ce = ret_res.get("tau_ce")
    uncalibrated = ret_res.get("uncalibrated", False)

    # If no corpus or insufficient logit, refuse IMMEDIATELY with zero generated text
    if status in ("no_corpus", "insufficient"):
        tier, rationale, _ = evaluate_evidence_tier([], top_logit=top_logit, tau_ce=tau_ce)
        norm_scores = {
            c["doc_id"]: c.get("normalized_relevance_score", 0.0) 
            for c in nearest if "doc_id" in c
        }
        return AskResponse(
            status=status,
            answer_sentences=[],
            tier=tier,
            tier_rationale=rationale,
            rank_breakdown=[],
            normalized_relevance_scores=norm_scores,
            nearest_documents=nearest,
            missing_conditions=[],
            refusal_reason=ret_res.get("refusal_reason"),
            uncalibrated=uncalibrated
        )

    # 3. Evidence Tier Assessment
    tier, rationale, _ = evaluate_evidence_tier(candidates, top_logit=top_logit, tau_ce=tau_ce)

    # 4. Transparent Ranking Breakdown
    ranked_candidates = rank_candidates(candidates)
    rank_items = []
    norm_scores = {}
    for r in ranked_candidates:
        bk = r.get("ranking", {})
        doc_id = r.get("doc_id", "unknown")
        norm_scores[doc_id] = r.get("normalized_relevance_score", 0.0)
        rank_items.append(RankItem(
            doc_id=doc_id,
            raw_logit=r.get("raw_logit"),
            s_rel=bk.get("s_rel", 0.0),
            s_corrob=bk.get("s_corrob", 0.0),
            s_source=bk.get("s_source", 0.0),
            weights=bk.get("weights", {}),
            rank_score=bk.get("rank_score", 0.0),
            distinct_groups_count=bk.get("distinct_groups_count", 0),
            has_contradiction=bk.get("has_contradiction", False),
            arithmetic_formula=bk.get("arithmetic_formula", ""),
            source_type_caveat=bk.get("source_type_caveat", "")
        ))

    # 5. Grounded Synthesis & Number Verification
    gen_res = generate_answer(query, ranked_candidates)
    gen_status = gen_res["status"]
    
    if gen_status == "needs_clarification":
        return AskResponse(
            status="needs_clarification",
            answer_sentences=[],
            tier=tier,
            tier_rationale=rationale,
            rank_breakdown=rank_items,
            normalized_relevance_scores=norm_scores,
            nearest_documents=ranked_candidates,
            missing_conditions=gen_res.get("missing_conditions", []),
            refusal_reason=gen_res.get("refusal_reason"),
            uncalibrated=uncalibrated
        )

    # Parse sentence objects and collect actually cited doc IDs
    answer_sentences = []
    cited_doc_ids = set()
    for s in gen_res.get("answer_sentences", []):
        citations = []
        for c in s.get("citations", []):
            d_id = c.get("doc_id")
            if d_id:
                cited_doc_ids.add(d_id)
                citations.append(Citation(
                    doc_id=d_id,
                    paper_title=c.get("paper_title"),
                    page=int(c["page"]) if c.get("page") is not None and str(c.get("page")).isdigit() else None
                ))
        answer_sentences.append(AnswerSentence(
            text=s.get("text", ""),
            citations=citations
        ))

    # Evidence tier strictly reflects the actual papers cited in generated sentences
    if answer_sentences and cited_doc_ids:
        cited_candidates = [c for c in ranked_candidates if c.get("doc_id") in cited_doc_ids]
        final_tier, final_rationale, _ = evaluate_evidence_tier(cited_candidates, top_logit=top_logit, tau_ce=tau_ce)
    else:
        final_tier, final_rationale = tier, rationale

    final_status = "answered" if answer_sentences else "insufficient"
    refusal_reason = gen_res.get("refusal_reason") if not answer_sentences else None

    return AskResponse(
        status=final_status,
        generation_mode=gen_res.get("generation_mode"),
        answer_sentences=answer_sentences,
        tier=final_tier,
        tier_rationale=final_rationale,
        rank_breakdown=rank_items,
        normalized_relevance_scores=norm_scores,
        nearest_documents=ranked_candidates,
        missing_conditions=[],
        refusal_reason=refusal_reason,
        uncalibrated=uncalibrated
    )
