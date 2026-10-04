import { useRef, useState } from "react";
import { api } from "../api";
import { BigButton, ErrorBanner, Shell, Spinner, useAction } from "../components/ui";
import { useApp } from "../store";

/** Shrink big phone photos (often 10 MB+) before upload. Falls back to the original file on any problem. */
async function shrinkImage(file: File): Promise<File | Blob> {
  if (!file.type.startsWith("image/") || file.size < 1_500_000) return file;
  try {
    const bmp = await createImageBitmap(file);
    const scale = Math.min(1, 2600 / Math.max(bmp.width, bmp.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bmp.width * scale); canvas.height = Math.round(bmp.height * scale);
    canvas.getContext("2d")!.drawImage(bmp, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((res) => canvas.toBlob(res, "image/jpeg", 0.88));
    return blob && blob.size < file.size ? new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" }) : file;
  } catch { return file; }
}

export default function ScanScreen() {
  const { t, lang, go } = useApp();
  const cameraInput = useRef<HTMLInputElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const [text, setText] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const scan = useAction((f: File | Blob) => api.scan(f, lang));
  const contract = useAction((x: string) => api.contract(x, lang));
  const notice = useAction((x: string) => api.notice(x, lang));

  const onFile = async (input: HTMLInputElement) => {
    const f = input.files?.[0];
    input.value = "";                                  // lets the same file be chosen again
    if (!f) return;
    setNote(null); setText(null);
    const r = await scan.run(await shrinkImage(f));
    if (r) { setText(r.text); setNote(r.note ?? (r.text ? null : t("noText"))); }
  };

  if (scan.busy) return <Shell title={t("scanDocument")}><Spinner label={t("scanning")} /></Shell>;
  if (contract.busy || notice.busy) return <Shell title={t("scanDocument")}><Spinner label={t("thinking")} /></Shell>;
  const ready = (text ?? "").trim().length >= 10;
  return <Shell title={t("scanDocument")} speak={t("scanHint")}>
    <p className="hint">{t("scanHint")}</p>
    <input ref={cameraInput} type="file" accept="image/*" capture="environment" hidden onChange={(e) => void onFile(e.currentTarget)} />
    <input ref={fileInput} type="file" accept="image/*,.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" hidden onChange={(e) => void onFile(e.currentTarget)} />
    <BigButton icon="📷" variant="primary" onClick={() => cameraInput.current?.click()}>{t("takePhoto")}</BigButton>
    <BigButton icon="📁" variant="primary" onClick={() => fileInput.current?.click()}>{t("chooseFile")}</BigButton>
    <p className="hint">{t("supportedDocuments")}</p>
    <ErrorBanner message={scan.error ?? contract.error ?? notice.error} />
    {note && <div className="notice">{note}</div>}
    {text !== null && text.length > 0 && <>
      <p className="big">{t("textFound")}</p>
      <textarea aria-label={t("textFound")} value={text} rows={8} maxLength={30000} onChange={(e) => setText(e.target.value)} />
      <BigButton variant="primary" disabled={!ready} onClick={async () => { const r = await contract.run(text); if (r) go({ name: "result", view: { kind: "contract", data: r } }); }}>{t("analyzeContract")}</BigButton>
      <BigButton disabled={!ready} onClick={async () => { const r = await notice.run(text); if (r) go({ name: "result", view: { kind: "notice", data: r } }); }}>{t("checkNotice")}</BigButton>
    </>}
  </Shell>;
}
