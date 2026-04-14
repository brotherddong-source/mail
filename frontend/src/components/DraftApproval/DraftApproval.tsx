"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { mailApi, DraftResponse } from "@/lib/api";

interface Props {
  draft: DraftResponse;
  mailId: string;
}

export default function DraftApproval({ draft, mailId }: Props) {
  const qc = useQueryClient();
  const [lang, setLang] = useState<"ko" | "en">("ko");
  const [body, setBody] = useState(
    lang === "ko" ? draft.generated_body_ko || "" : draft.generated_body_en || ""
  );
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  const handleLangChange = (l: "ko" | "en") => {
    setLang(l);
    setBody(l === "ko" ? draft.generated_body_ko || "" : draft.generated_body_en || "");
  };

  const approveMutation = useMutation({
    mutationFn: () =>
      mailApi.approveDraft(draft.id, {
        edited_body: body,
        use_ko: lang === "ko",
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

  const toList = draft.suggested_to || [];
  const ccList = draft.suggested_cc || [];

  return (
    <div className="space-y-4">
      {/* 수신자 추천 */}
      <div className="rounded-lg border p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">추천 수신자</h3>
        <div className="space-y-2">
          {toList.map((r, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700">TO</span>
              <span className="font-medium">{r.name || r.email}</span>
              <span className="text-gray-400">&lt;{r.email}&gt;</span>
              <span className="text-xs text-gray-400">— {r.reason}</span>
            </div>
          ))}
          {ccList.map((r, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600">CC</span>
              <span className="font-medium">{r.name || r.email}</span>
              <span className="text-gray-400">&lt;{r.email}&gt;</span>
            </div>
          ))}
          {toList.length === 0 && ccList.length === 0 && (
            <p className="text-xs text-gray-400">수신자 추천 없음</p>
          )}
        </div>
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
          disabled={approveMutation.isPending}
          className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {approveMutation.isPending ? "발송 중..." : "승인 후 발송"}
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
