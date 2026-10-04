import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, ApiError, setToken, setUnauthorizedHandler } from "./api";
import { lookup, translator, type Key } from "./i18n";
import type { Lang, LoginResult, Screen } from "./types";

interface Ctx {
  screen: Screen; go: (s: Screen) => void; back: () => void;
  lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string;
  session: LoginResult | null; login: (r: LoginResult) => void; logout: () => Promise<void>;
  errorText: (e: unknown) => string;
  bigText: boolean; setBigText: (b: boolean) => void; contrast: boolean; setContrast: (b: boolean) => void;
  sessionNotice: string | null;
}
const C = createContext<Ctx | null>(null);
export const useApp = () => { const c = useContext(C); if (!c) throw new Error("outside provider"); return c; };
const IDLE_WARN_MS = 60_000, IDLE_END_MS = 90_000;

export function AppProvider({ children }: { children: ReactNode }) {
  const [screen, setScreen] = useState<Screen>({ name: "language" });
  const history = useRef<Screen[]>([]);
  const [lang, setLang] = useState<Lang>("hi");
  const [session, setSession] = useState<LoginResult | null>(null);
  const [bigText, setBigText] = useState(false);
  const [contrast, setContrast] = useState(false);
  const [sessionNotice, setNotice] = useState<string | null>(null);
  const [idleWarn, setIdleWarn] = useState(false);
  const t = useMemo(() => translator(lang), [lang]);

  const go = useCallback((next: Screen) => { history.current.push(screen); setScreen(next); }, [screen]);
  const back = useCallback(() => { if (!history.current.length) return; const prev = history.current.pop()!; setScreen(prev); }, []);
  const reset = useCallback(() => { setToken(null); setSession(null); setIdleWarn(false); history.current = []; setScreen({ name: "language" }); }, []);
  const logout = useCallback(async () => { try { await api.logout(); } catch { /* ignore */ } reset(); }, [reset]);
  const login = useCallback((r: LoginResult) => { setToken(r.token); setSession(r); setNotice(null); history.current = []; setScreen({ name: "home" }); }, []);

  useEffect(() => { setUnauthorizedHandler(() => { setNotice(t("err.session_expired")); reset(); }); }, [reset, t]);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  useEffect(() => { document.documentElement.dataset.contrast = contrast ? "high" : "normal"; }, [contrast]);
  useEffect(() => { document.documentElement.style.fontSize = bigText ? "125%" : "100%"; }, [bigText]);

  useEffect(() => {
    if (!session) return;
    let warn = window.setTimeout(() => setIdleWarn(true), IDLE_WARN_MS);
    let end = window.setTimeout(() => { setNotice(t("err.session_expired")); void logout(); }, IDLE_END_MS);
    const bump = () => { setIdleWarn(false); clearTimeout(warn); clearTimeout(end); warn = window.setTimeout(() => setIdleWarn(true), IDLE_WARN_MS); end = window.setTimeout(() => { setNotice(t("err.session_expired")); void logout(); }, IDLE_END_MS); };
    const evs = ["pointerdown", "keydown"] as const;
    evs.forEach((e) => window.addEventListener(e, bump));
    return () => { clearTimeout(warn); clearTimeout(end); evs.forEach((e) => window.removeEventListener(e, bump)); };
  }, [session, logout, t]);

  const errorText = useCallback((e: unknown) => e instanceof ApiError ? (lookup(lang, "err." + (e.status === 0 ? "network" : e.code)) ?? e.message) : t("err.generic"), [t, lang]);
  const value: Ctx = { screen, go, back, lang, setLang, t, session, login, logout, errorText, bigText, setBigText, contrast, setContrast, sessionNotice };
  return <C.Provider value={value}>{children}{idleWarn && <div className="overlay" role="alertdialog" aria-live="assertive"><div className="dialog"><h2>{t("stillThere")}</h2><button className="big-btn primary" onClick={() => setIdleWarn(false)}>{t("tapToContinue")}</button></div></div>}</C.Provider>;
}