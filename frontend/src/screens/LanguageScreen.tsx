import { api } from "../api";
import { Shell } from "../components/ui";
import { LANGUAGES } from "../i18n";
import { useApp } from "../store";
import { useEffect, useState } from "react";

export default function LanguageScreen() {
  const { setLang, go, t, sessionNotice } = useApp();
  const [down, setDown] = useState(false);
  useEffect(() => { api.health().then((h) => setDown(h.status === "down")).catch(() => setDown(true)); }, []);
  return (
    <Shell title={`${t("appName")} • ${t("chooseLanguage")}`} back={false}>
      {sessionNotice && <div className="notice">{sessionNotice}</div>}
      {down && <div className="error" role="alert">⚠️ {t("err.network")}</div>}
      <div className="grid lang-grid">
        {LANGUAGES.map((l) => (
          <button key={l.code} className="big-btn lang" onClick={() => { setLang(l.code); go({ name: "login" }); }}>
            <span className="native">{l.native}</span><span className="sub">{l.english}</span>
          </button>
        ))}
      </div>
    </Shell>
  );
}
