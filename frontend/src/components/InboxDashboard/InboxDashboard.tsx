"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { mailApi, MailMessage } from "@/lib/api";
import MailRow from "./MailRow";
import MailDetail from "../MailDetail/MailDetail";
import Link from "next/link";
import { useAuth, logout } from "@/lib/auth";

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2, null: 3 };

export default function InboxDashboard() {
  const { user, loading } = useAuth();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-400">
        로딩 중...
      </div>
    );
  }

  const { data: mails = [], isLoading, refetch } = useQuery({
    queryKey: ["mails", statusFilter],
    queryFn: () => mailApi.list(statusFilter !== "all" ? { status: statusFilter } : {}),
    refetchInterval: 30_000,
  });

  const sorted = [...mails].sort(
    (a, b) =>
      (PRIORITY_ORDER[a.priority ?? "null"] ?? 3) -
      (PRIORITY_ORDER[b.priority ?? "null"] ?? 3)
  );

  const replyNeeded = mails.filter((m) => m.requires_reply).length;
  const high = mails.filter((m) => m.priority === "high").length;

  return (
    <div className="flex h-screen flex-col">
      {/* 헤더 */}
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">특허사무소 메일 인박스</h1>
            <p className="text-sm text-gray-500">
              전체 {mails.length}건 · 회신 필요 {replyNeeded}건 · 긴급 {high}건
            </p>
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

        {/* 필터 */}
        <div className="mt-3 flex gap-2">
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
      </header>

      {/* 본문 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 메일 목록 */}
        <div className="w-full overflow-y-auto border-r lg:w-1/2 xl:w-2/5">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center text-gray-400">
              로딩 중...
            </div>
          ) : sorted.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-gray-400">
              수신된 메일이 없습니다.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-50">
                <tr className="border-b text-xs text-gray-500">
                  <th className="px-4 py-2 text-left">수신시각</th>
                  <th className="px-4 py-2 text-left">발신자</th>
                  <th className="px-4 py-2 text-left">사건</th>
                  <th className="px-4 py-2 text-left">요약</th>
                  <th className="px-4 py-2 text-center">회신</th>
                  <th className="px-4 py-2 text-center">우선순위</th>
                  <th className="px-4 py-2 text-center">상태</th>
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

        {/* 상세 슬라이드오버 */}
        <div className="hidden flex-1 overflow-y-auto lg:block">
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
