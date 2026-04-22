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
    queryKey: ["mails", statusFilter, searchQuery],
    queryFn: () =>
      mailApi.list({
        ...(statusFilter !== "all" ? { status: statusFilter } : {}),
        ...(searchQuery ? { search: searchQuery } : {}),
      }),
    refetchInterval: 30_000,
    enabled: !loading && !!user,
  });

  // 검색 실행 (Enter 또는 버튼)
  const handleSearch = () => setSearchQuery(searchInput.trim());
  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };
  const clearSearch = () => {
    setSearchInput("");
    setSearchQuery("");
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

  // 필터 적용: 메일함 → 수신/발신 → 우선순위 → 회신필요
  let filtered = mails;
  if (mailboxFilter !== "all") {
    filtered = filtered.filter((m) => classifyMailbox(m) === mailboxFilter);
  }
  if (directionFilter !== "all") {
    filtered = filtered.filter((m) =>
      directionFilter === "outgoing" ? isOutgoingMail(m) : !isOutgoingMail(m)
    );
  }
  if (priorityFilter !== "all") {
    filtered = filtered.filter((m) => m.priority === priorityFilter);
  }
  if (replyFilter === "needed") {
    filtered = filtered.filter((m) => m.requires_reply);
  }

  const sorted = [...filtered].sort(
    (a, b) =>
      (PRIORITY_ORDER[a.priority ?? "null"] ?? 3) -
      (PRIORITY_ORDER[b.priority ?? "null"] ?? 3)
  );

  const replyNeeded = mails.filter((m) => m.requires_reply).length;
  const high = mails.filter((m) => m.priority === "high").length;
  const mailboxes: Mailbox[] = ["representative", "institutional", "personal"];

  // 활성 필터 개수
  const activeFilterCount =
    (mailboxFilter !== "all" ? 1 : 0) +
    (directionFilter !== "all" ? 1 : 0) +
    (priorityFilter !== "all" ? 1 : 0) +
    (replyFilter !== "all" ? 1 : 0) +
    (searchQuery ? 1 : 0);

  return (
    <div className="flex h-screen flex-col">
      {/* 헤더 */}
      <header className="border-b bg-white px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="IPLAB" className="h-8 object-contain" />
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => { setMailboxFilter("all"); setDirectionFilter("all"); setPriorityFilter("all"); setReplyFilter("all"); setStatusFilter("all"); clearSearch(); }}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                  activeFilterCount === 0 ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                전체 {mails.length}건
              </button>
              <span className="text-gray-300">|</span>
              <button
                onClick={() => setReplyFilter(replyFilter === "needed" ? "all" : "needed")}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                  replyFilter === "needed" ? "bg-orange-100 text-orange-700" : "text-gray-500 hover:bg-orange-50"
                }`}
              >
                회신 필요 {replyNeeded}건
              </button>
              <span className="text-gray-300">|</span>
              <button
                onClick={() => setPriorityFilter(priorityFilter === "high" ? "all" : "high")}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                  priorityFilter === "high" ? "bg-red-100 text-red-700" : "text-gray-500 hover:bg-red-50"
                }`}
              >
                긴급 {high}건
              </button>
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

        {/* 메일함별 통계 + 필터 영역 */}
        <div className="mt-2 flex items-start gap-4">
          {/* 메일함 카드 */}
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

          {/* 오른쪽: 필터 + 검색 */}
          <div className="flex flex-col gap-2 ml-auto items-end">
            {/* 검색 */}
            <div className="flex items-center gap-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={handleSearchKeyDown}
                  placeholder="제목, 발신자, 요약 검색..."
                  className="w-56 rounded-lg border px-3 py-1.5 text-xs text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-300"
                />
                {searchInput && (
                  <button
                    onClick={clearSearch}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
                  >
                    ✕
                  </button>
                )}
              </div>
              <button
                onClick={handleSearch}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
              >
                검색
              </button>
            </div>

            {/* 필터 행: 수신/발신 + 우선순위 + 상태 */}
            <div className="flex items-center gap-3">
              {/* 수신/발신 */}
              <div className="flex rounded-lg border p-0.5">
                {(["all", "incoming", "outgoing"] as Direction[]).map((d) => (
                  <button
                    key={d}
                    onClick={() => setDirectionFilter(d)}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                      directionFilter === d
                        ? "bg-blue-600 text-white"
                        : "text-gray-500 hover:bg-gray-100"
                    }`}
                  >
                    {d === "all" ? "전체" : d === "incoming" ? "수신" : "발신"}
                  </button>
                ))}
              </div>

              {/* 우선순위 */}
              <div className="flex gap-1">
                {(["all", "high", "medium", "low"] as PriorityFilter[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPriorityFilter(p === priorityFilter ? "all" : p)}
                    className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                      priorityFilter === p
                        ? p === "high"
                          ? "bg-red-600 text-white"
                          : p === "medium"
                          ? "bg-yellow-500 text-white"
                          : p === "low"
                          ? "bg-gray-500 text-white"
                          : "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                    }`}
                  >
                    {p === "all" ? "전체" : p === "high" ? "긴급" : p === "medium" ? "보통" : "낮음"}
                  </button>
                ))}
              </div>

              {/* 상태 */}
              <div className="flex gap-1">
                {["all", "pending", "analyzed", "draft_ready"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                      statusFilter === s
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {s === "all" ? "전체" : s === "pending" ? "처리중" : s === "analyzed" ? "분석완료" : "초안준비"}
                  </button>
                ))}
              </div>
            </div>

            {/* 필터 초기화 */}
            {activeFilterCount > 0 && (
              <button
                onClick={() => {
                  setMailboxFilter("all");
                  setDirectionFilter("all");
                  setPriorityFilter("all");
                  setReplyFilter("all");
                  setStatusFilter("all");
                  clearSearch();
                }}
                className="text-[10px] text-gray-400 hover:text-gray-600"
              >
                모든 필터 초기화 ({activeFilterCount}개 활성)
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
            <div className="flex h-32 flex-col items-center justify-center text-gray-400 gap-2">
              <span>
                {activeFilterCount > 0
                  ? "필터 조건에 맞는 메일이 없습니다."
                  : "수신된 메일이 없습니다."}
              </span>
              {activeFilterCount > 0 && (
                <button
                  onClick={() => {
                    setMailboxFilter("all");
                    setDirectionFilter("all");
                    setPriorityFilter("all");
                    setStatusFilter("all");
                    clearSearch();
                  }}
                  className="text-xs text-blue-500 hover:underline"
                >
                  필터 초기화
                </button>
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
