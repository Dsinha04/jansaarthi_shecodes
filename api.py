"""FastAPI service for Jansaarthi AI Core.  Run:  uvicorn api:app --host 0.0.0.0 --port 8001
Contract and examples: API_CONTRACT.md"""
import hmac
import logging
import threading
from typing import Literal, Optional
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import config
import fraud
import grievance
import risk
import schemes
from rag import RAGEngine

log = logging.getLogger(__name__)
DISCLAIMER = ("General information from official documents, not legal advice. "
              "Verify important decisions with your Registrar or a qualified professional.")

app = FastAPI(title="Jansaarthi AI Core")
if config.CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                       allow_methods=["GET", "POST"], allow_headers=["*"])

_engine = None
_lock = threading.Lock()


def require_key(x_api_key: Optional[str] = Header(None)):
    if config.SERVICE_KEY and not hmac.compare_digest(x_api_key or "", config.SERVICE_KEY):
        raise HTTPException(401, "Invalid or missing X-API-Key")


def get_engine():
    global _engine
    with _lock:                                   # avoid loading the model twice on parallel first requests
        if _engine is None:
            try:
                _engine = RAGEngine()
            except Exception as exc:              # missing index, model download failure, etc.
                log.exception("RAG engine failed to start")
                raise HTTPException(503, "Knowledge base not ready. Run ingest.py first.") from exc
    return _engine


def maybe_engine():
    """Engine if the knowledge base is available, else None (used by features that can work without it)."""
    if _engine is None and not config.FAISS_PATH.exists():
        return None
    try:
        return get_engine()
    except HTTPException:
        return None


class Question(BaseModel):
    text: str = Field(min_length=2, max_length=1000)
    language: str = Field("en", max_length=10)    # echoed back so the caller knows what to translate to


class Contract(BaseModel):
    text: str = Field(min_length=10, max_length=30000)
    explain: bool = False                         # let the API model explain the top flagged clauses
    language: str = Field("en", max_length=10)


class Notice(BaseModel):
    text: str = Field(min_length=5, max_length=5000)
    language: str = Field("en", max_length=10)


class Profile(BaseModel):
    owns_land: Optional[bool] = None
    occupation: list[Literal["farmer", "tenant_farmer", "sharecropper", "dairy", "fisher",
                             "poultry", "shg_member", "artisan", "other"]] = []
    is_society_member: Optional[bool] = None
    state: Optional[str] = Field(None, max_length=60)
    include_not_eligible: bool = False
    language: str = Field("en", max_length=10)


class GrievanceRequest(BaseModel):
    category: Literal["loan_dispute", "wrong_charges", "membership_shares",
                      "management_election", "fraud_misappropriation", "other"]
    society_type: Literal["state", "multi_state", "unknown"] = "unknown"
    member_name: Optional[str] = Field(None, max_length=80)
    society_name: Optional[str] = Field(None, max_length=120)
    member_no: Optional[str] = Field(None, max_length=30)
    details: Optional[str] = Field(None, max_length=2000)
    language: str = Field("en", max_length=10)


def _wrap(result, language):
    result["language"] = language
    result["disclaimer"] = DISCLAIMER
    return result


@app.get("/health")
def health():
    return {"ok": True, "index_ready": config.FAISS_PATH.exists(),
            "llm_configured": bool(config.LLM_API_KEY and config.LLM_MODEL and config.LLM_ENABLED)}


@app.post("/ask", dependencies=[Depends(require_key)])
def ask(q: Question):
    return _wrap(get_engine().ask(q.text), q.language)


@app.post("/analyze-contract", dependencies=[Depends(require_key)])
def analyze_contract(c: Contract):
    result = risk.analyze(c.text)
    result["explain_available"] = False
    if c.explain and result["findings"]:
        try:
            eng = get_engine()
        except HTTPException:
            eng = None                            # still return the rule-based flags
        if eng is not None:
            result["explain_available"] = True
            for f in result["findings"][:3]:      # limit API calls and cost
                f["legal_context"] = eng.ask(
                    "Explain in simple words what the following contract clause means for a cooperative "
                    "society member and what rights or procedures apply. Do not declare it legally valid "
                    f"or invalid.\nClause: \"\"\"{f['clause']}\"\"\"")
    return _wrap(result, c.language)


@app.post("/check-notice", dependencies=[Depends(require_key)])
def check_notice(n: Notice):
    return _wrap(fraud.analyze(n.text), n.language)


@app.post("/schemes/recommend", dependencies=[Depends(require_key)])
def recommend_schemes(p: Profile):
    profile = p.model_dump(exclude={"include_not_eligible", "language"})
    return _wrap(schemes.recommend(profile, include_not_eligible=p.include_not_eligible), p.language)


@app.post("/grievance/guide", dependencies=[Depends(require_key)])
def grievance_guide(g: GrievanceRequest):
    result = grievance.guide(g.category, g.society_type, g.member_name, g.society_name,
                             g.member_no, g.details, engine=maybe_engine())
    return _wrap(result, g.language)
