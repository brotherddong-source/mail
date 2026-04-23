"use client";
import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { mailApi, DraftResponse, SignatureItem } from "@/lib/api";
import TemplateSelector from "./TemplateSelector";
import SignatureSelector from "./SignatureSelector";

interface RecipientEntry {
  email: string;
  name: string;
}

interface Props {
  draft: DraftResponse;
  mailId: string;
  senderEmail?: string;
}

function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000);
    return () => clearTimeout(t);
  }, [onClose]);
  return (
    <div className="fixed bottom-6 right-6 z-50 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg">
      {message}
    </div>
  );
}

export default function DraftApproval({ draft, mailId, senderEmail = "ip@ip-lab.co.kr" }: Props) {
  const qc = useQueryClient();
  const [lang, setLang] = useState<"ko" | "en">("ko");

  // 한/영 독립 상태 — 언어 전환해도 편집 내용 유지
  const [bodyKo, setBodyKo] = useState(draft.generated_body_ko || "");
  const [bodyEn, setBodyEn] = useState(draft.generated_body_en || "");
  const currentBody = lang === "ko" ? bodyKo : bodyEn;
  const setCurrentBody = lang === "ko" ? setBodyKo : setBodyEn;

  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  // 템플릿 · 서명
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [selectedSig, setSelectedSig] = useState<SignatureItem | null>(null);
  const [showTemplatePanel, setShowTemplatePanel] = useState(false);
  const [customSigText, setCustomSigText] = useState("");
  const [useFreeSignature, setUseFreeSignature] = useState(false);

  // 수신자
  const [toList, setToList] = useState<RecipientEntry[]>(
    (draft.suggested_to || []).map((r) => ({ email: r.email, name: r.name || "" }))
  );
  const [ccList, setCcList] = useState<RecipientEntry[]>(
    (draft.suggested_cc || []).map((r) => ({ email: r.email, name: r.name || "" }))
  );
  const [newTo, setNewTo] = useState("");
  const [newCc, setNewCc] = useState("");

  const applySigToBody = (sigBody: string, setter: (fn: (prev: string) => string) => void) => {
    setter((prev) => {
      const withoutOldSig = prev.replace(/\n---sig---[\s\S]*$/, "");
      return withoutOldSig.trimEnd() + "\n---sig---\n" + sigBody;
    });
  };

  const handleSigSelect = (sig: SignatureItem) => {
    setSelectedSig(sig);
    setUseFreeSignature(false);
    if (sig.language === "ko") {
      applySigToBody(sig.body, setBodyKo);
    } else {
      applySigToBody(sig.body, setBodyEn);
    }
  };

  const applyCustomSig = () => {
    if (!customSigText) return;
    applySigToBody(customSigText, lang === "ko" ? setBodyKo : setBodyEn);
  };

  const regenerateMutation = useMutation({
    mutationFn: () =>
      mailApi.regenerateDraft(draft.id, {
        template_id: selectedTemplateId ?? undefined,
        signature_id: selectedSig?.id,
        sender_email: senderEmail,
      }),
    onSuccess: (data) => {
      setBodyKo(data.draft_ko);
      setBodyEn(data.draft_en);
      qc.invalidateQueries({ queryKey: ["mail", mailId] });
      setToast("초안이 재생성되었습니다.");
    },
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      mailApi.approveDraft(draft.id, {
        edited_body: currentBody,
        use_ko: lang === "ko",
        edited_to: toList,
        edited_cc: ccList,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mail", mailId] });
      qc.invalidateQueries({ queryKey: ["mails"] });
      setToast("발송이 완료되었습니다.");
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => mailApi.rejectDraft(draft.id, rejectReason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mail", mailId] });
    },
  });

  const addRecipient = (type: "to" | "cc") => {
    const value = (type === "to" ? newTo : newCc).trim();
    if (!value) return;
    const match = value.match(/^(.+?)\s*<(.+?)>$/) || value.match(/^(.+?)\s+(.+@.+)$/);
    const entry: RecipientEntry = match
      ? { name: match[1].trim(), email: match[2].trim() }
      : { name: "", email: value };
    if (type === "to") { setToList([...toList, entry]); setNewTo(""); }
    else { setCcList([...ccList, entry]); setNewCc(""); }
  };

  const updateRecipient = (
    type: "to" | "cc",
    idx: number,
    field: "email" | "name",
    val: string
  ) => {
    const setter = type === "to" ? setToList : setCcList;
    const list = type === "to" ? toList : ccList;
    const next = [...list];
    next[idx] = { ...next[idx], [field]: val };
    setter(next);
  };

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}

      {/* 템플릿 · 서명 패널 */}
      <div className="rounded-lg border p-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">초안 유형 · 서명</h3>
          <button
            onClick={() => setShowTemplatePanel(!showTemplatePanel)}
            className="rounded-md border px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
          >
            {showTemplatePanel ? "접기 ▲" : "선택 · 변경 ▼"}
          </button>
        </div>

        <div className="mt-2 flex flex-wrap gap-2">
          {selectedTemplateId ? (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">
              {selectedTemplateId.replace(/_/g, " ")}
            </span>
          ) : (
            <span className="text-[10px] text-gray-400">템플릿 미선택 (AI 자동 생성)</span>
          )}
          {selectedSig && (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700">
              {selectedSig.label}
            </span>
          )}
        </div>

        {showTemplatePanel && (
          <div className="mt-3 space-y-3">
            <TemplateSelector mailId={mailId} selectedId={selectedTemplateId} onSelect={setSelectedTemplateId} />
            <SignatureSelector
              senderEmail={senderEmail}
              selectedId={useFreeSignature ? null : (selectedSig?.id ?? null)}
              currentLang={lang}
              onSelect={handleSigSelect}
            />

            {/* 서명 직접 입력 */}
            <div className="rounded-lg border bg-gray-50 p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-600">서명 직접 입력</span>
                <button
                  onClick={() => setUseFreeSignature(!useFreeSignature)}
                  className="text-[10px] text-blue-500 hover:text-blue-700"
                >
                  {useFreeSignature ? "접기 ▲" : "펼치기 ▼"}
                </button>
              </div>
              {useFreeSignature && (
                <div className="space-y-2">
                  <textarea
                    value={customSigText}
                    onChange={(e) => setCustomSigText(e.target.value)}
                    rows={5}
                    placeholder={"예)\n홍길동 변리사\nIP LAB 특허법인\nTel: 02-000-0000"}
                    className="w-full rounded border bg-white p-2 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-300 resize-none"
                  />
                  <button
                    onClick={applyCustomSig}
                    className="w-full rounded border border-green-400 py-1.5 text-xs font-medium text-green-700 hover:bg-green-50 transition-colors"
                  >
                    이 서명 초안에 적용 ({lang === "ko" ? "국문" : "영문"})
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={() => regenerateMutation.mutate()}
              disabled={regenerateMutation.isPending}
              className="w-full rounded-lg border-2 border-blue-400 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50 disabled:opacity-50 transition-colors"
            >
              {regenerateMutation.isPending ? "재생성 중..." : "선택 내용으로 초안 재생성"}
            </button>
            {regenerateMutation.isError && (
              <p className="text-center text-xs text-red-500">재생성 실패. 다시 시도해주세요.</p>
            )}
          </div>
        )}
      </div>

      {/* 수신자 편집 */}
      <div className="rounded-lg border p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">수신자</h3>

        {/* TO */}
        <div className="mb-3">
          <div className="mb-1 text-xs font-medium text-gray-500">TO</div>
          <div className="space-y-1">
            {toList.map((r, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[9px] font-semibold text-blue-700 shrink-0">TO</span>
                <input
                  type="text"
                  value={r.name}
                  onChange={(e) => updateRecipient("to", i, "name", e.target.value)}
                  placeholder="이름"
                  className="w-20 shrink-0 rounded border px-1.5 py-1 text-xs text-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-300"
                />
                <input
                  type="text"
                  value={r.email}
                  onChange={(e) => updateRecipient("to", i, "email", e.target.value)}
                  className="flex-1 rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                />
                <button onClick={() => setToList(toList.filter((_, j) => j !== i))} className="text-xs text-red-400 hover:text-red-600 shrink-0">삭제</button>
              </div>
            ))}
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={newTo}
                onChange={(e) => setNewTo(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRecipient("to"))}
                placeholder="이메일 또는 이름 <email>"
                className="flex-1 rounded border border-dashed px-2 py-1 text-xs text-gray-500 placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-300"
              />
              <button onClick={() => addRecipient("to")} className="text-xs text-blue-500 hover:text-blue-700 shrink-0">추가</button>
            </div>
          </div>
        </div>

        {/* CC */}
        <div>
          <div className="mb-1 text-xs font-medium text-gray-500">CC</div>
          <div className="space-y-1">
            {ccList.map((r, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[9px] font-semibold text-gray-600 shrink-0">CC</span>
                <input
                  type="text"
                  value={r.name}
                  onChange={(e) => updateRecipient("cc", i, "name", e.target.value)}
                  placeholder="이름"
                  className="w-20 shrink-0 rounded border px-1.5 py-1 text-xs text-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-300"
                />
                <input
                  type="text"
                  value={r.email}
                  onChange={(e) => updateRecipient("cc", i, "email", e.target.value)}
                  className="flex-1 rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                />
                <button onClick={() => setCcList(ccList.filter((_, j) => j !== i))} className="text-xs text-red-400 hover:text-red-600 shrink-0">삭제</button>
              </div>
            ))}
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={newCc}
                onChange={(e) => setNewCc(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRecipient("cc"))}
                placeholder="이메일 또는 이름 <email>"
                className="flex-1 rounded border border-dashed px-2 py-1 text-xs text-gray-500 placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-300"
              />
              <button onClick={() => addRecipient("cc")} className="text-xs text-blue-500 hover:text-blue-700 shrink-0">추가</button>
            </div>
          </div>
        </div>

        {toList.length === 0 && (
          <p className="mt-2 text-xs text-red-400">TO 수신자가 없습니다. 최소 1명을 추가해주세요.</p>
        )}
      </div>

      {/* 초안 편집 — 언어 전환해도 편집 내용 유지 */}
      <div className="rounded-lg border p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">회신 초안</h3>
          <div className="flex gap-1 rounded-md border p-0.5">
            {(["ko", "en"] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${lang === l ? "bg-blue-600 text-white" : "text-gray-500 hover:bg-gray-100"}`}
              >
                {l === "ko" ? "국문" : "영문"}
              </button>
            ))}
          </div>
        </div>
        <textarea
          value={currentBody}
          onChange={(e) => setCurrentBody(e.target.value)}
          rows={14}
          className="w-full rounded border p-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none font-mono"
          placeholder="초안을 편집하세요..."
        />
      </div>

      {/* 승인/반려 */}
      <div className="flex gap-3">
        <button
          onClick={() => approveMutation.mutate()}
          disabled={approveMutation.isPending || toList.length === 0}
          title={toList.length === 0 ? "TO 수신자를 먼저 추가하세요" : undefined}
          className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {approveMutation.isPending ? "발송 중..." : `승인 후 발송 — TO ${toList.length}명`}
        </button>
        <button
          onClick={() => setShowReject(!showReject)}
          className={`rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors ${
            showReject ? "border-red-400 bg-red-50 text-red-600" : "text-gray-600 hover:bg-gray-50"
          }`}
        >
          반려
        </button>
      </div>

      {showReject && (
        <div className="space-y-2 rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="text-xs font-semibold text-red-700">반려 사유를 입력하세요</p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            placeholder="예: 수신자 확인 필요, 내용 수정 후 재요청..."
            className="w-full rounded border p-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-200"
          />
          <div className="flex gap-2">
            <button
              onClick={() => rejectMutation.mutate()}
              disabled={rejectMutation.isPending}
              className="flex-1 rounded-lg bg-red-500 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
            >
              {rejectMutation.isPending ? "처리 중..." : "반려 확정"}
            </button>
            <button onClick={() => setShowReject(false)} className="rounded-lg border px-4 py-2 text-sm text-gray-500 hover:bg-gray-50">취소</button>
          </div>
        </div>
      )}

      {approveMutation.isError && (
        <p className="text-center text-sm text-red-600">발송 실패. 다시 시도해주세요.</p>
      )}
    </div>
  );
}
