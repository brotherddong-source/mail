"use client";
import { useState } from "react";
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
  senderEmail?: string; // 발신자 (서명 선택에 사용)
}

export default function DraftApproval({ draft, mailId, senderEmail = "ip@ip-lab.co.kr" }: Props) {
  const qc = useQueryClient();
  const [lang, setLang] = useState<"ko" | "en">("ko");
  const [body, setBody] = useState(
    lang === "ko" ? draft.generated_body_ko || "" : draft.generated_body_en || ""
  );
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  // 템플릿 · 서명 선택 상태
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [selectedSig, setSelectedSig] = useState<SignatureItem | null>(null);
  const [showTemplatePanel, setShowTemplatePanel] = useState(false);
  const [customSigText, setCustomSigText] = useState("");
  const [useFreeSignature, setUseFreeSignature] = useState(false);

  // 수신자 상태 관리
  const [toList, setToList] = useState<RecipientEntry[]>(
    (draft.suggested_to || []).map((r) => ({ email: r.email, name: r.name || "" }))
  );
  const [ccList, setCcList] = useState<RecipientEntry[]>(
    (draft.suggested_cc || []).map((r) => ({ email: r.email, name: r.name || "" }))
  );
  const [newTo, setNewTo] = useState("");
  const [newCc, setNewCc] = useState("");

  const handleLangChange = (l: "ko" | "en") => {
    setLang(l);
    setBody(l === "ko" ? draft.generated_body_ko || "" : draft.generated_body_en || "");
  };

  const handleSigSelect = (sig: SignatureItem) => {
    setSelectedSig(sig);
    setUseFreeSignature(false);
    setBody((prev) => {
      const withoutOldSig = prev.replace(/\n---sig---[\s\S]*$/, "");
      return withoutOldSig.trimEnd() + "\n---sig---\n" + sig.body;
    });
  };

  const applyCustomSig = () => {
    setBody((prev) => {
      const withoutOldSig = prev.replace(/\n---sig---[\s\S]*$/, "");
      return withoutOldSig.trimEnd() + (customSigText ? "\n---sig---\n" + customSigText : "");
    });
  };

  const regenerateMutation = useMutation({
    mutationFn: () =>
      mailApi.regenerateDraft(draft.id, {
        template_id: selectedTemplateId ?? undefined,
        signature_id: selectedSig?.id,
        sender_email: senderEmail,
      }),
    onSuccess: (data) => {
      const newBody = lang === "ko" ? data.draft_ko : data.draft_en;
      setBody(newBody);
      qc.invalidateQueries({ queryKey: ["mail", mailId] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      mailApi.approveDraft(draft.id, {
        edited_body: body,
        use_ko: lang === "ko",
        edited_to: toList,
        edited_cc: ccList,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mail", mailId] });
      qc.invalidateQueries({ queryKey: ["mails"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => mailApi.rejectDraft(draft.id, rejectReason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mail", mailId] });
    },
  });

  const addRecipient = (type: "to" | "cc") => {
    const value = type === "to" ? newTo.trim() : newCc.trim();
    if (!value) return;
    // "이름 <email>" 또는 "email" 형식 파싱
    const match = value.match(/^(.+?)\s*<(.+?)>$/) || value.match(/^(.+?)\s+(.+@.+)$/);
    const entry: RecipientEntry = match
      ? { name: match[1].trim(), email: match[2].trim() }
      : { name: "", email: value };

    if (type === "to") {
      setToList([...toList, entry]);
      setNewTo("");
    } else {
      setCcList([...ccList, entry]);
      setNewCc("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, type: "to" | "cc") => {
    if (e.key === "Enter") {
      e.preventDefault();
      addRecipient(type);
    }
  };

  const removeTo = (idx: number) => setToList(toList.filter((_, i) => i !== idx));
  const removeCc = (idx: number) => setCcList(ccList.filter((_, i) => i !== idx));

  const updateToEmail = (idx: number, email: string) => {
    const next = [...toList];
    next[idx] = { ...next[idx], email };
    setToList(next);
  };

  const updateCcEmail = (idx: number, email: string) => {
    const next = [...ccList];
    next[idx] = { ...next[idx], email };
    setCcList(next);
  };

  return (
    <div className="space-y-4">

      {/* 템플릿 · 서명 선택 패널 */}
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

        {/* 현재 선택 요약 (항상 표시) */}
        <div className="mt-2 flex flex-wrap gap-2">
          {selectedTemplateId ? (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">
              📄 {selectedTemplateId.replace(/_/g, " ")}
            </span>
          ) : (
            <span className="text-[10px] text-gray-400">템플릿 미선택 (AI 자동 생성)</span>
          )}
          {selectedSig && (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700">
              ✍️ {selectedSig.label}
            </span>
          )}
        </div>

        {showTemplatePanel && (
          <div className="mt-3 space-y-3">
            <TemplateSelector
              mailId={mailId}
              selectedId={selectedTemplateId}
              onSelect={setSelectedTemplateId}
            />
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
                    placeholder={"예)\n홍길동 변리사\nIP LAB 특허법인\nTel: 02-000-0000\nemail@ip-lab.co.kr"}
                    className="w-full rounded border bg-white p-2 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-300 resize-none"
                  />
                  <button
                    onClick={applyCustomSig}
                    className="w-full rounded border border-green-400 py-1.5 text-xs font-medium text-green-700 hover:bg-green-50 transition-colors"
                  >
                    이 서명 초안에 적용
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={() => regenerateMutation.mutate()}
              disabled={regenerateMutation.isPending}
              className="w-full rounded-lg border-2 border-blue-400 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50 disabled:opacity-50 transition-colors"
            >
              {regenerateMutation.isPending ? "재생성 중..." : "🔄 선택 내용으로 초안 재생성"}
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
              <div key={i} className="flex items-center gap-2">
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 shrink-0">TO</span>
                <input
                  type="text"
                  value={r.email}
                  onChange={(e) => updateToEmail(i, e.target.value)}
                  className="flex-1 rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                />
                {r.name && <span className="text-xs text-gray-400 shrink-0">{r.name}</span>}
                <button
                  onClick={() => removeTo(i)}
                  className="text-xs text-red-400 hover:text-red-600 shrink-0"
                >
                  삭제
                </button>
              </div>
            ))}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newTo}
                onChange={(e) => setNewTo(e.target.value)}
                onKeyDown={(e) => handleKeyDown(e, "to")}
                placeholder="이메일 추가 (Enter로 추가)"
                className="flex-1 rounded border border-dashed px-2 py-1 text-xs text-gray-500 placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-300"
              />
              <button
                onClick={() => addRecipient("to")}
                className="text-xs text-blue-500 hover:text-blue-700 shrink-0"
              >
                추가
              </button>
            </div>
          </div>
        </div>

        {/* CC */}
        <div>
          <div className="mb-1 text-xs font-medium text-gray-500">CC</div>
          <div className="space-y-1">
            {ccList.map((r, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600 shrink-0">CC</span>
                <input
                  type="text"
                  value={r.email}
                  onChange={(e) => updateCcEmail(i, e.target.value)}
                  className="flex-1 rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                />
                {r.name && <span className="text-xs text-gray-400 shrink-0">{r.name}</span>}
                <button
                  onClick={() => removeCc(i)}
                  className="text-xs text-red-400 hover:text-red-600 shrink-0"
                >
                  삭제
                </button>
              </div>
            ))}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newCc}
                onChange={(e) => setNewCc(e.target.value)}
                onKeyDown={(e) => handleKeyDown(e, "cc")}
                placeholder="이메일 추가 (Enter로 추가)"
                className="flex-1 rounded border border-dashed px-2 py-1 text-xs text-gray-500 placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-300"
              />
              <button
                onClick={() => addRecipient("cc")}
                className="text-xs text-blue-500 hover:text-blue-700 shrink-0"
              >
                추가
              </button>
            </div>
          </div>
        </div>

        {toList.length === 0 && (
          <p className="mt-2 text-xs text-red-400">TO 수신자가 없습니다. 최소 1명을 추가해주세요.</p>
        )}
      </div>

      {/* 초안 편집 */}
      <div className="rounded-lg border p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">회신 초안</h3>
          <div className="flex gap-1 rounded-md border p-0.5">
            <button
              onClick={() => handleLangChange("ko")}
              className={`rounded px-2 py-0.5 text-xs font-medium ${lang === "ko" ? "bg-blue-600 text-white" : "text-gray-500"}`}
            >
              국문
            </button>
            <button
              onClick={() => handleLangChange("en")}
              className={`rounded px-2 py-0.5 text-xs font-medium ${lang === "en" ? "bg-blue-600 text-white" : "text-gray-500"}`}
            >
              영문
            </button>
          </div>
        </div>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={12}
          className="w-full rounded border p-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
          placeholder="초안을 편집하세요..."
        />
      </div>

      {/* 승인/반려 버튼 */}
      <div className="flex gap-3">
        <button
          onClick={() => approveMutation.mutate()}
          disabled={approveMutation.isPending || toList.length === 0}
          className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {approveMutation.isPending ? "발송 중..." : `승인 후 발송 (TO: ${toList.length}명)`}
        </button>
        <button
          onClick={() => setShowReject(!showReject)}
          className="rounded-lg border px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
        >
          반려
        </button>
      </div>

      {/* 반려 사유 입력 */}
      {showReject && (
        <div className="space-y-2">
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={3}
            placeholder="반려 사유를 입력하세요..."
            className="w-full rounded border p-3 text-sm focus:outline-none focus:ring-2 focus:ring-red-200"
          />
          <button
            onClick={() => rejectMutation.mutate()}
            disabled={rejectMutation.isPending}
            className="w-full rounded-lg bg-red-500 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
          >
            {rejectMutation.isPending ? "처리 중..." : "반려 확정"}
          </button>
        </div>
      )}

      {approveMutation.isSuccess && (
        <p className="text-center text-sm text-green-600 font-medium">발송 완료!</p>
      )}
      {approveMutation.isError && (
        <p className="text-center text-sm text-red-600">발송 실패. 다시 시도해주세요.</p>
      )}
    </div>
  );
}
