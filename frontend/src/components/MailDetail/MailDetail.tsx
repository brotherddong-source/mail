"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  mailApi,
  caseApi,
  classifyMailbox,
  isOutgoingMail as checkOutgoing,
  MAILBOX_LABEL,
  MAILBOX_COLOR,
  MailMessage,
  CaseInfo,
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

function formatSummary(text: string): string {
  if (text.includes("\n")) return text;
  return text.replace(/([.?!。])\s+/g, "$1\n");
}

// ── 사건 정보 패널 ─────────────────────────────────────────────────
function CasePanel({
  mailId,
  caseInfo,
  onLinked,
}: {
  mailId: string;
  caseInfo: CaseInfo | null;
  onLinked: () => void;
}) {
  const queryClient = useQueryClient();
  const [linking, setLinking] = useState(false);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(false);

  const { data: searchResults, isFetching } = useQuery({
    queryKey: ["case-search", search],
    queryFn: () => caseApi.list(search),
    enabled: linking && search.length >= 2,
  });

  const linkMutation = useMutation({
    mutationFn: (caseNumber: string | null) => mailApi.linkCase(mailId, caseNumber),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mail", mailId] });
      setLinking(false);
      setSearch("");
      onLinked();
    },
  });

  if (caseInfo && !linking) {
    const isOverdue = caseInfo.deadline && new Date(caseInfo.deadline) < new Date();
    return (
      <div className="border rounded-lg overflow-hidden text-xs">
        {/* 헤더 */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="w-full flex items-center justify-between px-3 py-2 bg-blue-50 hover:bg-blue-100 transition-colors"
        >
          <span className="font-semibold text-blue-800 flex items-center gap-2">
            {caseInfo.case_number}
            {caseInfo.your_ref && <span className="font-mono font-normal text-blue-500">/ {caseInfo.your_ref}</span>}
            {caseInfo.client_name && <span className="font-normal text-blue-600">— {caseInfo.client_name}</span>}
            {isOverdue && <span className="rounded bg-red-100 px-1.5 py-0.5 text-[9px] font-bold text-red-600">마감 초과</span>}
          </span>
          <span className="text-blue-400">{expanded ? "▲" : "▼"}</span>
        </button>

        {expanded && (
          <div className="bg-white">
            {/* 사건 정보 테이블 */}
            <table className="w-full border-collapse">
              <tbody>
                {/* 행 1: 명칭 */}
                {(caseInfo.title_ko || caseInfo.title_en) && (
                  <tr className="border-b">
                    <td className="w-20 bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">발명명칭</td>
                    <td className="px-3 py-1.5 text-gray-800" colSpan={3}>
                      {caseInfo.title_ko && <div>{caseInfo.title_ko}</div>}
                      {caseInfo.title_en && <div className="text-gray-500 italic">{caseInfo.title_en}</div>}
                    </td>
                  </tr>
                )}
                {/* 행 2: Our Ref / Your Ref */}
                <tr className="border-b">
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">Our Ref.</td>
                  <td className="px-3 py-1.5 font-mono text-blue-700">{caseInfo.case_number}</td>
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">Your Ref.</td>
                  <td className="px-3 py-1.5 font-mono text-gray-700">{caseInfo.your_ref || "-"}</td>
                </tr>
                {/* 행 3: 출원번호 / 등록번호 */}
                <tr className="border-b">
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">출원번호</td>
                  <td className="px-3 py-1.5 font-mono text-gray-700">{caseInfo.app_number || "-"}</td>
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">등록번호</td>
                  <td className="px-3 py-1.5 font-mono text-gray-700">{caseInfo.reg_number || "-"}</td>
                </tr>
                {/* 행 4: 국가 / 권리유형 */}
                <tr className="border-b">
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">국가</td>
                  <td className="px-3 py-1.5 text-gray-700">{caseInfo.country || "-"}</td>
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">권리유형</td>
                  <td className="px-3 py-1.5 text-gray-700">{caseInfo.case_type || "-"}</td>
                </tr>
                {/* 행 5: 상태 / 담당변리사 */}
                <tr className="border-b">
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">상태</td>
                  <td className="px-3 py-1.5 text-gray-700">{caseInfo.status || "-"}</td>
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">담당변리사</td>
                  <td className="px-3 py-1.5 text-gray-700">{caseInfo.attorney || "-"}</td>
                </tr>
                {/* 행 6: 마감일 / 출원일 */}
                <tr className="border-b">
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">마감일</td>
                  <td className={`px-3 py-1.5 font-medium ${isOverdue ? "text-red-600" : "text-gray-700"}`}>
                    {caseInfo.deadline || "-"}
                    {isOverdue && " ⚠"}
                  </td>
                  <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">출원일</td>
                  <td className="px-3 py-1.5 text-gray-700">{caseInfo.filed_at || "-"}</td>
                </tr>
                {/* 행 6b: 등록일 / 우선일 */}
                {(caseInfo.registered_at || caseInfo.priority_date) && (
                  <tr className="border-b">
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">등록일</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.registered_at || "-"}</td>
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">우선일</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.priority_date || "-"}</td>
                  </tr>
                )}
                {/* 행 6c: 공지예외일 / 공개일 */}
                {(caseInfo.public_notice_exception_date || caseInfo.published_at) && (
                  <tr className="border-b">
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">공지예외일</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.public_notice_exception_date || "-"}</td>
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">공개일</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.published_at || "-"}</td>
                  </tr>
                )}
                {/* 행 6d: 심사청구일 / 심사청구기한 */}
                {(caseInfo.exam_request_date || caseInfo.exam_request_deadline) && (
                  <tr className="border-b">
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">심사청구일</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.exam_request_date || "-"}</td>
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">심사청구기한</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.exam_request_deadline || "-"}</td>
                  </tr>
                )}
                {/* 행 6e: 국제출원일 / 국내단계진입일 */}
                {(caseInfo.intl_filed_at || caseInfo.national_phase_at) && (
                  <tr className="border-b">
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">국제출원일</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.intl_filed_at || "-"}</td>
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">국내단계진입</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.national_phase_at || "-"}</td>
                  </tr>
                )}
                {/* 행 7: 출원인 / 출원인담당 */}
                {(caseInfo.applicant || caseInfo.applicant_contact) && (
                  <tr className="border-b">
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">출원인</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.applicant || "-"}</td>
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">출원인담당</td>
                    <td className="px-3 py-1.5 text-gray-700">{caseInfo.applicant_contact || "-"}</td>
                  </tr>
                )}
                {/* 비고 */}
                {caseInfo.notes && (
                  <tr className="border-b">
                    <td className="bg-gray-50 px-3 py-1.5 font-medium text-gray-500 whitespace-nowrap">비고</td>
                    <td className="px-3 py-1.5 text-gray-600" colSpan={3}>{caseInfo.notes}</td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* 액션 버튼 */}
            <div className="flex gap-3 px-3 py-2 border-t bg-gray-50">
              <button onClick={() => setLinking(true)} className="text-blue-600 hover:underline">
                사건 변경
              </button>
              <button onClick={() => linkMutation.mutate(null)} className="text-gray-400 hover:text-red-500">
                연결 해제
              </button>
              {linkMutation.isPending && <span className="text-gray-400">처리 중...</span>}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 연결 없거나 변경 모드
  return (
    <div className="border border-dashed rounded-lg px-3 py-2 text-xs">
      {!linking ? (
        <div className="flex items-center justify-between">
          <span className="text-gray-400">사건 미매칭</span>
          <button
            onClick={() => setLinking(true)}
            className="text-blue-600 hover:underline font-medium"
          >
            + 사건 연결
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="사건번호 또는 고객사 검색..."
              className="flex-1 border rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <button
              onClick={() => { setLinking(false); setSearch(""); }}
              className="text-gray-400 hover:text-gray-600"
            >
              취소
            </button>
          </div>
          {isFetching && <p className="text-gray-400">검색 중...</p>}
          {searchResults && searchResults.length > 0 && (
            <ul className="border rounded divide-y max-h-40 overflow-y-auto">
              {searchResults.slice(0, 20).map((c) => (
                <li key={c.id}>
                  <button
                    onClick={() => linkMutation.mutate(c.case_number)}
                    className="w-full text-left px-2 py-1.5 hover:bg-blue-50 transition-colors"
                  >
                    <span className="font-mono font-semibold text-blue-700">{c.case_number}</span>
                    <span className="ml-2 text-gray-500">{c.client_name}</span>
                    {c.status && <span className="ml-1 text-gray-400">({c.status})</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {searchResults && searchResults.length === 0 && search.length >= 2 && (
            <p className="text-gray-400">검색 결과 없음</p>
          )}
          {linkMutation.isError && (
            <p className="text-red-500">{String((linkMutation.error as any)?.response?.data?.detail || "연결 실패")}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ── 번역 패널 ─────────────────────────────────────────────────────
function TranslationPanel({ mailId, translation }: { mailId: string; translation: string | null }) {
  const queryClient = useQueryClient();
  const translateMutation = useMutation({
    mutationFn: () => mailApi.translate(mailId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["mail", mailId] }),
  });

  if (translation) {
    return (
      <div className="space-y-3">
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{translation}</p>
        </div>
        <button
          onClick={() => translateMutation.mutate()}
          disabled={translateMutation.isPending}
          className="text-xs text-blue-500 hover:underline disabled:opacity-50"
        >
          {translateMutation.isPending ? "번역 중..." : "다시 번역"}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3 h-40 text-center">
      <p className="text-sm text-gray-400">번역이 없습니다.</p>
      <button
        onClick={() => translateMutation.mutate()}
        disabled={translateMutation.isPending}
        className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {translateMutation.isPending ? "번역 중..." : "AI로 번역 요청"}
      </button>
      {translateMutation.isError && (
        <p className="text-xs text-red-500">번역 실패. 다시 시도해주세요.</p>
      )}
    </div>
  );
}

// ── 초안 없음 패널 ────────────────────────────────────────────────
function NoDraftPanel({ mailId, hasPast }: { mailId: string; hasPast: boolean }) {
  const queryClient = useQueryClient();
  const createMutation = useMutation({
    mutationFn: () => mailApi.createDraft(mailId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["mail", mailId] }),
  });

  return (
    <div className="flex flex-col items-center justify-center gap-3 h-40 text-center">
      <p className="text-sm text-gray-400">
        {hasPast ? "이미 처리된 초안입니다." : "AI가 생성한 초안이 없습니다."}
      </p>
      {!hasPast && (
        <button
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {createMutation.isPending ? "생성 중..." : "직접 작성하기"}
        </button>
      )}
      {createMutation.isError && (
        <p className="text-xs text-red-500">
          {String((createMutation.error as any)?.response?.data?.detail || "생성 실패")}
        </p>
      )}
    </div>
  );
}

// ── 메인 컴포넌트 ──────────────────────────────────────────────────
export default function MailDetail({ mailId, onClose }: Props) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("summary");
  const [outgoingOverride, setOutgoingOverride] = useState<boolean | null>(null);

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
            <div className="flex items-center gap-2 flex-wrap">
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

            {/* 사건 정보 패널 */}
            <div className="mt-2">
              <CasePanel
                mailId={mailId}
                caseInfo={mail.case_info ?? null}
                onLinked={() => queryClient.invalidateQueries({ queryKey: ["mail", mailId] })}
              />
            </div>
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
              {t === "summary" ? "AI 요약" : t === "original" ? "원문" : t === "translation" ? "번역" : (
                <span className="flex items-center gap-1">
                  초안
                  {pendingDraft && <span className="inline-block w-1.5 h-1.5 rounded-full bg-orange-500" />}
                </span>
              )}
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
          <div className="prose prose-sm max-w-none">
            {mail.body_html ? (
              <div dangerouslySetInnerHTML={{ __html: mail.body_html }} />
            ) : (
              <pre className="whitespace-pre-wrap text-sm text-gray-700">{mail.body_text}</pre>
            )}
          </div>
        )}

        {tab === "translation" && (
          <TranslationPanel mailId={mailId} translation={mail.ai_translation} />
        )}

        {tab === "draft" && (
          pendingDraft ? (
            <DraftApproval draft={pendingDraft} mailId={mailId} senderEmail={replyFromEmail} />
          ) : (
            <NoDraftPanel mailId={mailId} hasPast={!!mail.drafts?.length} />
          )
        )}
      </div>
    </div>
  );
}
