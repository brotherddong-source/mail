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

type Direction = "all" | "incoming" | "outgoing";
type PriorityFilter = "all" | "high" | "medium" | "low";
type ReplyFilter = "all" | "needed";

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
  const [directionFilter, setDirectionFilter] = useState<Direction>("all");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");
  const [replyFilter, setReplyFilter] = useState<ReplyFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");

  // --- 메일목록·상세 리사이즈 ---
  const [listWidthPercent, setListWidthPercent] = useState(50);
  const contentRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current || !contentRef.current) return;
      const rect = contentRef.current.getBoundingClientRect();
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
    queryKey: ["mails", statusFilter, searchQuery],
    queryFn: () =>
      mailApi.list({
        ...(statusFilter !== "all" ? { status: statusFilter } : {}),
        ...(searchQuery ? { search: searchQuery } : {}),
      }),
    refetchInterval: 30_000,
    enabled: !loading && !!user,
  });

  const handleSearch = () => setSearchQuery(searchInput.trim());
  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };
  const clearSearch = () => { setSearchInput(""); setSearchQuery(""); };
  const resetAll = () => {
    setMailboxFilter("all");
    setDirectionFilter("all");
    setPriorityFilter("all");
    setReplyFilter("all");
    setStatusFilter("all");
    clearSearch();
  };

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
      if (out) totalStats[box].outgoing++; else totalStats[box].incoming++;
      if (m.received_at && new Date(m.received_at) >= todayStart) {
        todayStats[box].total++;
        if (out) todayStats[box].outgoing++; else todayStats[box].incoming++;
      }
    }
    return { todayStats, totalStats };
  }, [mails]);

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-gray-400">로딩 중...</div>;
  }

  // 필터 적용
  let filtered = mails;
  if (mailboxFilter !== "all") filtered = filtered.filter((m) => classifyMailbox(m) === mailboxFilter);
  if (directionFilter !== "all") filtered = filtered.filter((m) => directionFilter === "outgoing" ? isOutgoingMail(m) : !isOutgoingMail(m));
  if (priorityFilter !== "all") filtered = filtered.filter((m) => m.priority === priorityFilter);
  if (replyFilter === "needed") filtered = filtered.filter((m) => m.requires_reply);

  const sorted = [...filtered].sort(
    (a, b) => (PRIORITY_ORDER[a.priority ?? "null"] ?? 3) - (PRIORITY_ORDER[b.priority ?? "null"] ?? 3)
  );

  const replyNeeded = mails.filter((m) => m.requires_reply).length;
  const urgentCount = mails.filter((m) => m.priority === "high").length;
  const mailboxes: Mailbox[] = ["representative", "institutional", "personal"];

  const activeFilterCount =
    (mailboxFilter !== "all" ? 1 : 0) +
    (directionFilter !== "all" ? 1 : 0) +
    (priorityFilter !== "all" ? 1 : 0) +
    (replyFilter !== "all" ? 1 : 0) +
    (searchQuery ? 1 : 0);

  return (
    <div className="flex h-screen flex-col">
      {/* ── 헤더 (얇게) ── */}
      <header className="flex h-12 shrink-0 items-center justify-between border-b bg-white px-4 shadow-sm">
        <div className="flex items-center gap-3">
          <img src="/logo.png" alt="IPLAB" className="h-7 object-contain" />
          <span className="text-xs text-gray-400">
            전체 {mails.length}건 · 회신필요 {replyNeeded}건 · 긴급 {urgentCount}건
          </span>
        </div>
        <div className="flex items-center gap-2">
          {user && (
            <div className="flex items-center gap-1.5 text-sm text-gray-600">
              <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-semibold text-blue-700">
                {user.name[0]}
              </div>
              <span className="text-xs">{user.name}</span>
            </div>
          )}
          <Link href="/cases" className="rounded border px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50">사건관리</Link>
          <Link href="/settings/signatures" className="rounded border px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50">서명관리</Link>
          <button onClick={() => refetch()} className="rounded border px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50">새로고침</button>
          <button onClick={logout} className="rounded border px-2.5 py-1 text-xs text-red-500 hover:bg-red-50">로그아웃</button>
        </div>
      </header>

      {/* ── 본문: 왼쪽 필터 사이드바 + 메일 목록 + 상세 ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── 왼쪽 필터 사이드바 ── */}
        <aside className="flex w-44 shrink-0 flex-col gap-4 overflow-y-auto border-r bg-gray-50 px-3 py-4">

          {/* 검색 */}
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">검색</p>
            <div className="flex flex-col gap-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={handleSearchKeyDown}
                  placeholder="제목·발신자·요약"
                  className="w-full rounded border bg-white px-2 py-1.5 text-xs text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-300"
                />
                {searchInput && (
                  <button onClick={clearSearch} className="absolute right-1.5 top-1/2 -translate-y-1/2 text-gray-300 hover:text-gray-500 text-xs">✕</button>
                )}
              </div>
              <button
                onClick={handleSearch}
                className="rounded bg-blue-600 py-1 text-xs font-medium text-white hover:bg-blue-700"
              >
                검색
              </button>
            </div>
          </div>

          {/* 메일함 */}
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">메일함</p>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => setMailboxFilter("all")}
                className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${mailboxFilter === "all" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-200"}`}
              >
                전체 <span className="float-right opacity-70">{mails.length}</span>
              </button>
              {mailboxes.map((box) => {
                const color = MAILBOX_COLOR[box];
                const isActive = mailboxFilter === box;
                return (
                  <button
                    key={box}
                    onClick={() => setMailboxFilter(isActive ? "all" : box)}
                    className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${
                      isActive ? `${color.bg} ${color.text} ring-1 ring-inset ring-current` : "text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${color.dot}`} />
                    {MAILBOX_LABEL[box]}
                    <span className="float-right opacity-70">{totalStats[box].total}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 수신 / 발신 */}
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">수신 · 발신</p>
            <div className="flex flex-col gap-1">
              {(["all", "incoming", "outgoing"] as Direction[]).map((d) => (
                <button
                  key={d}
                  onClick={() => setDirectionFilter(d)}
                  className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${
                    directionFilter === d ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {d === "all" ? "전체" : d === "incoming" ? "수신" : "발신"}
                </button>
              ))}
            </div>
          </div>

          {/* 우선순위 */}
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">우선순위</p>
            <div className="flex flex-col gap-1">
              {([
                { v: "all", label: "전체", cls: "bg-blue-600 text-white", idle: "text-gray-600" },
                { v: "high", label: `긴급 (${urgentCount})`, cls: "bg-red-500 text-white", idle: "text-red-500 hover:bg-red-50" },
                { v: "medium", label: "보통", cls: "bg-yellow-500 text-white", idle: "text-yellow-600 hover:bg-yellow-50" },
                { v: "low", label: "낮음", cls: "bg-gray-500 text-white", idle: "text-gray-500 hover:bg-gray-200" },
              ] as { v: PriorityFilter; label: string; cls: string; idle: string }[]).map(({ v, label, cls, idle }) => (
                <button
                  key={v}
                  onClick={() => setPriorityFilter(v === priorityFilter && v !== "all" ? "all" : v)}
                  className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${
                    priorityFilter === v ? cls : idle
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 회신 필요 */}
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">회신</p>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => setReplyFilter("all")}
                className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${replyFilter === "all" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-200"}`}
              >
                전체
              </button>
              <button
                onClick={() => setReplyFilter(replyFilter === "needed" ? "all" : "needed")}
                className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${
                  replyFilter === "needed" ? "bg-orange-500 text-white" : "text-orange-600 hover:bg-orange-50"
                }`}
              >
                회신 필요 ({replyNeeded})
              </button>
            </div>
          </div>

          {/* 처리 상태 */}
          <div>
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">처리 상태</p>
            <div className="flex flex-col gap-1">
              {[
                { v: "all", label: "전체" },
                { v: "pending", label: "처리 중" },
                { v: "analyzed", label: "분석 완료" },
                { v: "draft_ready", label: "초안 준비" },
              ].map(({ v, label }) => (
                <button
                  key={v}
                  onClick={() => setStatusFilter(v)}
                  className={`rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${
                    statusFilter === v ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 필터 초기화 */}
          {activeFilterCount > 0 && (
            <button
              onClick={resetAll}
              className="rounded border border-gray-300 py-1.5 text-xs text-gray-500 hover:bg-white transition-colors"
            >
              초기화 ({activeFilterCount})
            </button>
          )}
        </aside>

        {/* ── 메일 목록 + 상세 ── */}
        <div ref={contentRef} className="flex flex-1 overflow-hidden">
          {/* 메일 목록 */}
          <div className="overflow-y-auto border-r" style={{ width: `${listWidthPercent}%` }}>
            {isLoading ? (
              <div className="flex h-32 items-center justify-center text-gray-400">로딩 중...</div>
            ) : sorted.length === 0 ? (
              <div className="flex h-32 flex-col items-center justify-center gap-2 text-gray-400">
                <span>{activeFilterCount > 0 ? "필터 조건에 맞는 메일이 없습니다." : "수신된 메일이 없습니다."}</span>
                {activeFilterCount > 0 && (
                  <button onClick={resetAll} className="text-xs text-blue-500 hover:underline">필터 초기화</button>
                )}
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-50">
                  <tr className="border-b text-xs text-gray-500">
                    <th className="px-2 py-2 text-center w-12">구분</th>
                    <th className="px-3 py-2 text-left">시각</th>
                    <th className="px-3 py-2 text-left">발신자</th>
                    <th className="px-3 py-2 text-left">담당자</th>
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

          {/* 상세 */}
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
    </div>
  );
}
