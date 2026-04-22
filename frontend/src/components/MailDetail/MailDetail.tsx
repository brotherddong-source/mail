"use client";
import { useQuery } from "@tanstack/react-query";
import {
  mailApi,
  classifyMailbox,
  isOutgoingMail as checkOutgoing,
  MAILBOX_LABEL,
  MAILBOX_COLOR,
  MailMessage,
} from "@/lib/api";
import { format } from "date-fns";
import { ko } from "date-fns/locale";
import DraftApproval from "../DraftApproval/DraftApproval";
import { useState, useEffect } from "react";

interface Props {
  mailId: string;
  onClose: () => void;
}

type Tab = "summary" | "original" | "translation" | "draft";

/** AI 요약 텍스트를 문장 단위로 줄바꿈 처리 */
function formatSummary(text: string): string {
  // 이미 줄바꿈이 있으면 그대로 유지
  if (text.includes("\n")) return text;
  // 마침표/물음표/느낌표 뒤에 공백이 오면 줄바꿈 삽입
  return text.replace(/([.?!。])\s+/g, "$1\n");
}

export default function MailDetail({ mailId, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("summary");
  const [outgoingOverride, setOutgoingOverride] = useState<boolean | null>(null);

  // 메일이 바뀌면 오버라이드 초기화
  useEffect(() => { setOutgoingOverride(null); }, [mailId]);

  const { data: mail, isLoading } = useQuery({
    queryKey: ["mail", mailId],
    queryFn: () => mailApi.detail(mailId),
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        불러오는 중...
      </div>
    );
  }
  if (!mail) return null;

  const receivedAt = mail.received_at
    ? format(new Date(mail.received_at), "yyyy.MM.dd HH:mm", { locale: ko })
    : "-";

  const autoOutgoing = checkOutgoing(mail as unknown as MailMessage);
  const outgoing = outgoingOverride ?? autoOutgoing;
  const mailbox = classifyMailbox(mail as unknown as MailMessage);
  const mbColor = MAILBOX_COLOR[mailbox];

  // 회신 발신자: 수신메일이면 받은 ip-lab 주소, 발신메일이면 from_email
  const replyFromEmail = outgoing
    ? (mail.from_email ?? "ip@ip-lab.co.kr")
    : (mail.to_emails?.find((e) => e.address?.toLowerCase().endsWith("@ip-lab.co.kr"))?.address ?? "ip@ip-lab.co.kr");

  const pendingDraft = mail.drafts?.find((d) => d.approval_status === "pending");

  return (
    <div className="flex h-full flex-col bg-white">
      {/* 헤더 */}
      <div className="border-b px-6 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-gray-900 truncate">{mail.subject}</h2>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${mbColor.bg} ${mbColor.text}`}>
                {MAILBOX_LABEL[mailbox]}
              </span>
              <button
                onClick={() => setOutgoingOverride(outgoing ? false : true)}
                title="클릭하여 수신/발신 변경"
                className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold transition-colors ${
                  outgoing
                    ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                    : "bg-blue-100 text-blue-700 hover:bg-blue-200"
                }`}
              >
                {outgoing ? "발신 ✎" : "수신 ✎"}
              </button>
              {outgoingOverride !== null && (
                <button
                  onClick={() => setOutgoingOverride(null)}
                  className="text-[10px] text-gray-400 hover:text-gray-600"
                  title="자동 감지로 되돌리기"
                >
                  초기화
                </button>
              )}
            </div>
            <div className="mt-1 text-sm text-gray-500">
              {mail.from_name} &lt;{mail.from_email}&gt; · {receivedAt}
            </div>
            {mail.to_emails?.length > 0 && (
              <div className="mt-0.5 text-xs text-gray-400">
                To: {mail.to_emails.map((e) => e.name || e.address).join(", ")}
              </div>
            )}
            {mail.cc_emails?.length > 0 && (
              <div className="text-xs text-gray-400">
                Cc: {mail.cc_emails.map((e) => e.name || e.address).join(", ")}
              </div>
            )}
            {mail.case_number && (
              <div className="mt-1 text-xs text-blue-700 font-mono">
                사건: {mail.case_number} ({mail.client_name})
              </div>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 shrink-0">✕</button>
        </div>

        {/* 탭 */}
        <div className="mt-3 flex gap-1">
          {(["summary", "original", "translation", "draft"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === t ? "bg-blue-600 text-white" : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              {t === "summary" ? "AI 요약" : t === "original" ? "원문" : t === "translation" ? "번역" : `초안${pendingDraft ? " ●" : ""}`}
            </button>
          ))}
        </div>
      </div>

      {/* 탭 콘텐츠 */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {tab === "summary" && (
          <div className="space-y-4">
            <div className="rounded-lg bg-blue-50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-blue-800">AI 요약</h3>
              <p className="text-sm text-blue-900 leading-relaxed whitespace-pre-line">
                {mail.ai_summary ? formatSummary(mail.ai_summary) : "(요약 없음)"}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded border p-3">
                <div className="text-xs text-gray-400 mb-1">분류</div>
                <div className="font-medium">{mail.ai_classification || "-"}</div>
              </div>
              <div className="rounded border p-3">
                <div className="text-xs text-gray-400 mb-1">우선순위</div>
                <div className={`font-medium ${mail.priority === "high" ? "text-red-600" : mail.priority === "medium" ? "text-yellow-600" : "text-gray-600"}`}>
                  {mail.priority === "high" ? "긴급" : mail.priority === "medium" ? "보통" : mail.priority === "low" ? "낮음" : "-"}
                </div>
              </div>
              <div className="rounded border p-3">
                <div className="text-xs text-gray-400 mb-1">회신 필요</div>
                <div className={`font-medium ${mail.requires_reply ? "text-orange-600" : "text-gray-400"}`}>
                  {mail.requires_reply ? "필요" : "불필요"}
                </div>
              </div>
              <div className="rounded border p-3">
                <div className="text-xs text-gray-400 mb-1">처리 상태</div>
                <div className="font-medium">{mail.processing_status}</div>
              </div>
            </div>
          </div>
        )}

        {tab === "original" && (
          <div className="space-y-3">
            {mail.has_attachments && (
              <div className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-700">
                이 메일에 첨부파일이 있습니다. 첨부파일/인라인 이미지는 Microsoft Graph API를 통해 별도 다운로드가 필요합니다.
              </div>
            )}
            <div className="prose prose-sm max-w-none">
              {mail.body_html ? (
                <div dangerouslySetInnerHTML={{ __html: mail.body_html }} />
              ) : (
                <pre className="whitespace-pre-wrap text-sm text-gray-700">{mail.body_text}</pre>
              )}
            </div>
          </div>
        )}

        {tab === "translation" && (
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {mail.ai_translation || "(번역 없음 — 원문이 한국어이거나 번역이 생성되지 않았습니다.)"}
            </p>
          </div>
        )}

        {tab === "draft" && (
          pendingDraft ? (
            <DraftApproval draft={pendingDraft} mailId={mailId} senderEmail={replyFromEmail} />
          ) : (
            <div className="flex h-32 items-center justify-center text-gray-400">
              {mail.drafts?.length ? "이미 처리된 초안입니다." : "초안이 없습니다."}
            </div>
          )
        )}
      </div>
    </div>
  );
}
