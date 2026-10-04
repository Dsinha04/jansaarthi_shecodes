import type { AskResult, ComplaintResult, ContractResult, Lang, LoginResult, NoticeResult, ProfileResult, SchemesResult } from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

let token: string | null = null;
let onUnauthorized: (() => void) | null = null;
export const setToken = (t: string | null) => { token = t; };
export const setUnauthorizedHandler = (fn: () => void) => { onUnauthorized = fn; };

async function request<T>(method: string, path: string, body?: unknown, form?: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res: Response;
  try {
    res = await fetch(`${BASE}/api${path}`, { method, headers, body: form ?? (body !== undefined ? JSON.stringify(body) : undefined) });
  } catch { throw new ApiError(0, "network", "Cannot reach the server."); }
  if (!res.ok) {
    let code = "http_" + res.status, msg = "Something went wrong.";
    try { const j = await res.json(); code = j.error?.code ?? code; msg = j.error?.message ?? msg; } catch { /* non-JSON error */ }
    if (res.status === 401 && token && (code === "session_expired" || code === "session_invalid" || code === "not_logged_in")) onUnauthorized?.();
    throw new ApiError(res.status, code, msg);
  }
  return res.json() as Promise<T>;
}

export interface HealthResult { status: "ok" | "degraded" | "down"; components: Record<string, { ok: boolean }> }

export const api = {
  health: () => request<HealthResult>("GET", "/health"),
  loginRfid: (uid: string, language: Lang) => request<LoginResult>("POST", "/auth/rfid", { uid, language }),
  loginFingerprint: (language: Lang) => request<LoginResult>("POST", "/auth/fingerprint", { language }),
  loginGuest: (language: Lang) => request<LoginResult>("POST", "/auth/guest", { language }),
  register: (p: { name: string; phone: string; address: string; profession: string; land_owned: boolean; land_area?: string; society_name?: string }, language: Lang) =>
    request<{ registration_id: number; status: "pending"; message: string }>("POST", "/auth/register", { ...p, language }),
  logout: () => request<{ ok: boolean }>("POST", "/auth/logout"),
  profile: () => request<ProfileResult>("GET", "/auth/profile"),
  transcribe: (audio: Blob, language: Lang) => { const f = new FormData(); f.append("audio", audio, "voice.webm"); f.append("language", language); return request<{ text: string; engine: string; note?: string }>("POST", "/speech/transcribe", undefined, f); },
  scan: (file: Blob, language: Lang) => { const f = new FormData(); f.append("file", file, file instanceof File ? file.name : "scan"); f.append("language", language); return request<{ document_id: number; text: string; engine: string; note?: string }>("POST", "/ocr/scan", undefined, f); },
  ask: (text: string, language: Lang) => request<AskResult>("POST", "/ai/ask", { text, language }),
  contract: (text: string, language: Lang, explain = false) => request<ContractResult>("POST", "/ai/contract", { text, language, explain }),
  notice: (text: string, language: Lang) => request<NoticeResult>("POST", "/ai/notice", { text, language }),
  schemes: (p: { owns_land: boolean | null; occupation: string[]; other_occupation?: string; is_society_member: boolean | null; state?: string }, language: Lang) => request<SchemesResult>("POST", "/ai/schemes", { ...p, language }),
  complaint: (p: { category: string; society_type: string; member_name?: string; society_name?: string; member_no?: string; details?: string }, language: Lang) => request<ComplaintResult>("POST", "/complaints", { ...p, language }),
  preview: (req: object) => request<{ receipt: string }>("POST", "/receipt/preview", req),
  print: (req: object) => request<{ printed: boolean; reason: string | null; receipt: string }>("POST", "/print", req),
};