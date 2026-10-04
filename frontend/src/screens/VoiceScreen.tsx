import { useRef, useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, useAction } from "../components/ui";
import { useApp } from "../store";

export default function VoiceScreen() {
  const { t, lang, go } = useApp();
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const rec = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const stt = useAction((b: Blob) => api.transcribe(b, lang));
  const ask = useAction((q: string) => api.ask(q, lang));

  const start = async () => {
    setMicError(null); setNote(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunks.current = [];
      mr.ondataavailable = (e) => chunks.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        const r = await stt.run(new Blob(chunks.current, { type: mr.mimeType || "audio/webm" }));
        if (r) { if (r.text) setText(r.text); else setNote(r.note ?? t("noText")); }
      };
      mr.start(); rec.current = mr; setRecording(true);
    } catch { setMicError(t("err.microphone")); }
  };
  const stop = () => { rec.current?.stop(); setRecording(false); };

  const submit = async () => {
    const r = await ask.run(text.trim());
    if (r) go({ name: "result", view: { kind: "ask", data: r } });
  };

  if (stt.busy) return <Shell title={t("askByVoice")}><Spinner label={t("transcribing")} /></Shell>;
  if (ask.busy) return <Shell title={t("askByVoice")}><Spinner label={t("thinking")} /></Shell>;
  return (
    <Shell title={t("askByVoice")} speak={t("tapToSpeak")}>
      <button className={`mic ${recording ? "live" : ""}`} onClick={recording ? stop : () => void start()}
              aria-label={recording ? t("recording") : t("tapToSpeak")}>🎤</button>
      <p className="big center">{recording ? t("recording") : t("tapToSpeak")}</p>
      <ErrorBanner message={micError ?? stt.error ?? ask.error} />
      {note && <div className="notice">{note}</div>}
      <textarea aria-label={t("typeInstead")} placeholder={t("typeInstead")} value={text} maxLength={1000} rows={4}
                onChange={(e) => setText(e.target.value)} />
      <BigButton variant="primary" disabled={text.trim().length < 2} onClick={() => void submit()}>{t("askNow")}</BigButton>
    </Shell>
  );
}
