from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from .config import SUPPORTED_LANGUAGES
Lang = str

def _check_lang(v: str) -> str:
    if v not in SUPPORTED_LANGUAGES: raise ValueError(f"language must be one of {SUPPORTED_LANGUAGES}")
    return v
class LangMixin(BaseModel):
    language: str = "en"; _v = field_validator("language")(_check_lang)
class RfidLogin(LangMixin): uid: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9:_-]+$")
class FingerprintLogin(LangMixin): template_id: Optional[int] = Field(None, ge=0, le=100000)
class GuestLogin(LangMixin): pass
class LanguageUpdate(LangMixin): pass
class RegistrationIn(LangMixin):
    name: str = Field(min_length=2, max_length=100); phone: str = Field(min_length=10, max_length=15, pattern=r"^[0-9]+$")
    address: str = Field(min_length=3, max_length=300); profession: str = Field(min_length=2, max_length=100)
    land_owned: bool; land_area: Optional[str] = Field(None, max_length=50); society_name: Optional[str] = Field(None, max_length=120)
class TranslateIn(BaseModel): text: str = Field(min_length=1, max_length=5000); source: str = "auto"; target: str = "en"
class AskIn(LangMixin): text: str = Field(min_length=2, max_length=1000)
class ContractIn(LangMixin): text: str = Field(min_length=10, max_length=30000); explain: bool = False
class NoticeIn(LangMixin): text: str = Field(min_length=5, max_length=5000)
class SchemesIn(LangMixin):
    owns_land: Optional[bool] = None
    occupation: list[Literal["farmer", "tenant_farmer", "sharecropper", "dairy", "fisher", "poultry", "shg_member", "artisan", "other"]] = []
    other_occupation: Optional[str] = Field(None, max_length=100)
    is_society_member: Optional[bool] = None; state: Optional[str] = Field(None, max_length=60); include_not_eligible: bool = False
Category = Literal["loan_dispute", "wrong_charges", "membership_shares", "management_election", "fraud_misappropriation", "other"]
class ComplaintIn(LangMixin):
    category: Category; society_type: Literal["state", "multi_state", "unknown"] = "unknown"; member_name: Optional[str] = Field(None, max_length=80)
    society_name: Optional[str] = Field(None, max_length=120); member_no: Optional[str] = Field(None, max_length=30); details: Optional[str] = Field(None, max_length=2000)
class PrintIn(BaseModel):
    kind: Literal["complaint", "answer", "text"]; complaint_id: Optional[int] = None; conversation_id: Optional[int] = None; text: Optional[str] = Field(None, max_length=8000); title: Optional[str] = Field(None, max_length=100)