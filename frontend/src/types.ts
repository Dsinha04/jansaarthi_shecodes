export type Lang = "en" | "hi" | "bn" | "mr" | "ta" | "te" | "gu" | "pa";

export const CATEGORIES = [
  "loan_dispute",
  "wrong_charges",
  "membership_shares",
  "management_election",
  "fraud_misappropriation",
  "other",
] as const;
export type Category = (typeof CATEGORIES)[number];

export const OCCUPATIONS = [
  "farmer",
  "tenant_farmer",
  "sharecropper",
  "dairy",
  "fisher",
  "poultry",
  "shg_member",
  "artisan",
  "other",
] as const;
export type Occupation = (typeof OCCUPATIONS)[number];

/* ---------- Auth / profile ---------- */

export interface User {
  id: number;
  name: string;
  member_no: string | null;
  phone: string | null;
  address: string | null;
  society_name: string | null;
  profession: string | null;
  land_owned: boolean | null;
  land_area: string | null;
  registration_status: "pending" | "approved" | string;
  is_active: boolean;
  pending_schemes: string[];
  preferred_language?: string | null;
}

export interface LoginResult {
  token: string;
  expires_at: string;
  method: string;
  language: Lang;
  user: User | null;
}

export interface ComplaintSummary {
  id: number;
  reference: string;
  category: string;
  status: string;
  created_at: string;
  details: string | null;
}

export interface OwnedDocument {
  id: number;
  filename: string;
  created_at: string;
}

export interface ProfileResult {
  user: User;
  complaints: ComplaintSummary[];
  pending_schemes: string[];
  owned_documents: OwnedDocument[];
}

/* ---------- AI results (shared fields) ---------- */

interface AiBase {
  language: string;
  disclaimer: string;
  translation_ok?: boolean;
  conversation_id?: number;
}

export interface Source {
  n: number;
  file: string;
  page: number | null;
  section: string | null;
  score?: number;
  excerpt: string;
}

export interface AskResult extends AiBase {
  answer: string;
  sources: Source[];
  mode: "full" | "retrieval_only" | "no_evidence";
  grounded: boolean;
  top_score?: number;
}

export interface ContractFinding {
  rule: string;
  severity: "high" | "medium" | "low" | string;
  title: string;
  clause: string;
  explanation: string;
}

export interface ContractResult extends AiBase {
  risk_level: "none" | "low" | "medium" | "high";
  score: number;
  findings: ContractFinding[];
  explain_available?: boolean;
}

export interface NoticeFlag {
  rule: string;
  severity: string;
  title: string;
  match: string;
  explanation: string;
}

export interface NoticeResult extends AiBase {
  verdict: "likely_fraud" | "suspicious" | "low_concern" | "no_flags";
  score: number;
  flags: NoticeFlag[];
  advice: string[];
  note: string | null;
}

export interface Scheme {
  id: string;
  name: string;
  summary: string;
  status: "likely_eligible" | "check_details" | "not_eligible";
  checks: { label: string; result: string }[];
  exclusions: string[];
  documents: string[];
  where_to_apply: string;
  source_url: string;
  verified: boolean;
}

export interface SchemesResult extends AiBase {
  schemes: Scheme[];
  note: string;
}

export interface GuideResult {
  category: string;
  label: string;
  steps: { n: number; title: string; detail: string }[];
  evidence: { file: string; page: number | null; section: string | null; excerpt: string }[];
  complaint_template: string;
  note: string;
  language: string;
  disclaimer: string;
}

export interface ComplaintResult {
  id: number;
  reference: string;
  guide: GuideResult;
  letter_english: string;
  translation_ok: boolean;
}

/* ---------- Navigation ---------- */

export type ResultView =
  | { kind: "ask"; data: AskResult }
  | { kind: "contract"; data: ContractResult }
  | { kind: "notice"; data: NoticeResult }
  | { kind: "schemes"; data: SchemesResult }
  | { kind: "complaint"; data: ComplaintResult };

export type ReceiptReq =
  | { kind: "answer"; conversation_id: number }
  | { kind: "complaint"; complaint_id: number }
  | { kind: "text"; text: string; title?: string };

export type Screen =
  | { name: "language" }
  | { name: "login" }
  | { name: "register" }
  | { name: "home" }
  | { name: "voice" }
  | { name: "scan" }
  | { name: "schemes" }
  | { name: "complaint" }
  | { name: "result"; view: ResultView }
  | { name: "receipt"; req: ReceiptReq };