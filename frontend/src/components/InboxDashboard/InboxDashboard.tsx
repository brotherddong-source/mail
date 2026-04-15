"use client";
import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  mailApi,
  MailMessage,
  Mailbox,
  classifyMailbox,
  isOutgoingMail,
  MAILBOX_LABEL,
  MAILBOX_COLOR,
} from "@/lib/api";
import MailRow from "./MailRow";
import MailDetail from "../MailDetail/MailDetail";
import Link from "next/link";
import { useAuth, logout } from "@/lib/auth";

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2, null: 3 };

interface MailboxStats {
  total: number;
  incoming: number;
  outgoing: number;
}

export default function InboxDashboard() {
  const { user, loading } = useAuth();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [mailboxFilter, setMailboxFilter] = useState<Mailbox | "all">("all");

  // --- 리사이즈 ---
  const [listWidthPercent, setListWidthPercent] = useState(45);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const percent = ((e.clientX - rect.left) / rect.width) * 100;
      setListWidthPercent(Math.min(Math.max(percent, 25), 75));
    };
    const handleMouseUp = () => {
      if (isDragging.current) {
        isDragging.current = false;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  const { data: mails = [], isLoading, refetch } = useQuery({
    queryKey: ["mails", statusFilter],
    queryFn: () => mailApi.list(statusFilter !== "all" ? { status: statusFilter } : {}),
    refetchInterval: 30_000,
    enabled: !loading && !!user,
  });

  // --- 메일함별 통계 ---
  const { todayStats, totalStats } = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const empty = (): Record<Mailbox, MailboxStats> => ({
      representative: { total: 0, incoming: 0, outgoing: 0 },
      institutional: { total: 0, incoming: 0, outgoing: 0 },
      personal: { total: 0, incoming: 0, outgoing: 0 },
    });

    const todayStats = empty();
    const totalStats = empty();

    for (const m of mails) {
      const box = classifyMailbox(m);
      const out = isOutgoingMail(m);
      totalStats[box].total++;
      if (out) totalStats[box].outgoing++;
      else totalStats[box].incoming++;

      if (m.received_at && new Date(m.received_at) >= todayStart) {
        todayStats[box].total++;
        if (out) todayStats[box].outgoing++;
        else todayStats[box].incoming++;
      }
    }

    return { todayStats, totalStats };
  }, [mails]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-400">
        로딩 중...
      </div>
    );
  }

  // 메일함 필터 적용
  const filtered = mailboxFilter === "all"
    ? mails
    : mails.filter((m) => classifyMailbox(m) === mailboxFilter);

  const sorted = [...filtered].sort(
    (a, b) =>
      (PRIORITY_ORDER[a.priority ?? "null"] ?? 3) -
      (PRIORITY_ORDER[b.priority ?? "null"] ?? 3)
  );

  const replyNeeded = mails.filter((m) => m.requires_reply).length;
  const high = mails.filter((m) => m.priority === "high").length;

  const mailboxes: Mailbox[] = ["representative", "institutional", "personal"];

  return (
    <div className="flex h-screen flex-col">
      {/* 헤더 */}
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="IPLAB" className="h-8 object-contain" />
            <div>
              <p className="text-sm text-gray-500">
                전체 {mails.length}건 · 회신 필요 {replyNeeded}건 · 긴급 {high}건
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {user && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center font-semibold text-blue-700">
                  {user.name[0]}
                </div>
                <span>{user.name}</span>
                {user.department && <span className="text-xs text-gray-400">({user.department})</span>}
              </div>
            )}
            <Link href="/cases" className="rounded-md border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
              사건 관리
            </Link>
            <button onClick={() => refetch()} className="rounded-md border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
              새로고침
            </button>
            <button onClick={logout} className="rounded-md border px-3 py-2 text-sm text-red-500 hover:bg-red-50">
              로그아웃
            </button>
          </div>
        </div>

        {/* 메일함별 통계 (3행) */}
        <div className="mt-3 flex items-start gap-4">
          <div className="grid grid-cols-3 gap-2 text-xs">
            {mailboxes.map((box) => {
              const color = MAILBOX_COLOR[box];
              const today = todayStats[box];
              const total = totalStats[box];
              const isActive = mailboxFilter === box;
              return (
                <button
                  key={box}
                  onClick={() => setMailboxFilter(isActive ? "all" : box)}
                  className={`rounded-lg px-3 py-2 text-left transition-all ${
                    isActive
                      ? `${color.bg} ring-2 ring-offset-1 ring-current ${color.text}`
                      : `${color.bg} ${color.text} hover:ring-1 hover:ring-gray-300`
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className={`inline-block h-2 w-2 rounded-full ${color.dot}`} />
                    <span className="font-semibold">{MAILBOX_LABEL[box]}</span>
                    <span className="ml-auto font-bold text-sm">{total.total}</span>
                  </div>
                  <div className="flex gap-2 text-[10px] opacity-75">
                    <span>오늘 {today.total}</span>
                    <span>(수신 {today.incoming} / 발신 {today.outgoing})</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* 상태 필터 */}
          <div className="flex flex-col gap-1.5 ml-auto">
            <div className="flex gap-2">
              {["all", "pending", "analyzed", "draft_ready"].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    statusFilter === s
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {s === "all" ? "전체" : s === "pending" ? "처리 중" : s === "analyzed" ? "분석 완료" : "초안 준비"}
                </button>
              ))}
            </div>
            {mailboxFilter !== "all" && (
              <button
                onClick={() => setMailboxFilter("all")}
                className="text-[10px] text-gray-400 hover:text-gray-600 self-end"
              >
                메일함 필터 해제
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 본문 */}
      <div ref={containerRef} className="flex flex-1 overflow-hidden">
        {/* 메일 목록 */}
        <div
          className="overflow-y-auto border-r"
          style={{ width: `${listWidthPercent}%` }}
        >
          {isLoading ? (
            <div className="flex h-32 items-center justify-center text-gray-400">
              로딩 중...
            </div>
          ) : sorted.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-gray-400">
              {mailboxFilter !== "all"
                ? `${MAILBOX_LABEL[mailboxFilter]}에 해당하는 메일이 없습니다.`
                : "수신된 메일이 없습니다."}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-50">
                <tr className="border-b text-xs text-gray-500">
                  <th className="px-2 py-2 text-center w-12">구분</th>
                  <th className="px-3 py-2 text-left">시각</th>
                  <th className="px-3 py-2 text-left">발신자</th>
                  <th className="px-3 py-2 text-left">사건</th>
                  <th className="px-3 py-2 text-left">요약</th>
                  <th className="px-3 py-2 text-center">회신</th>
                  <th className="px-3 py-2 text-center">우선순위</th>
                  <th className="px-3 py-2 text-center">상태</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((mail) => (
                  <MailRow
                    key={mail.id}
                    mail={mail}
                    selected={selectedId === mail.id}
                    onClick={() => setSelectedId(mail.id)}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* 리사이즈 핸들 */}
        <div
          onMouseDown={handleMouseDown}
          className="hidden lg:flex w-1.5 cursor-col-resize items-center justify-center hover:bg-blue-100 active:bg-blue-200 transition-colors bg-gray-100 shrink-0"
        >
          <div className="h-8 w-0.5 rounded-full bg-gray-300" />
        </div>

        {/* 상세 슬라이드오버 */}
        <div className="hidden flex-1 overflow-y-auto lg:block min-w-0">
          {selectedId ? (
            <MailDetail mailId={selectedId} onClose={() => setSelectedId(null)} />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-400">
              메일을 선택하면 상세 내용이 표시됩니다.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
