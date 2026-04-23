"use client";
import { useRef, useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { caseApi, Case, Contact } from "@/lib/api";
import Link from "next/link";

type UploadType = "cases" | "contacts";
type ViewTab = "cases" | "contacts";
type DeadlineFilter = "all" | "overdue" | "soon";
type DeadlineSort = "asc" | "desc" | null;

const STATUS_COLORS: Record<string, string> = {
  출원중: "bg-blue-100 text-blue-700",
  심사중: "bg-indigo-100 text-indigo-700",
  등록: "bg-green-100 text-green-700",
  등록됨: "bg-green-100 text-green-700",
  거절: "bg-red-100 text-red-600",
  포기: "bg-gray-100 text-gray-500",
  취하: "bg-gray-100 text-gray-500",
  심판: "bg-orange-100 text-orange-700",
  유지: "bg-teal-100 text-teal-700",
};

const ROLE_LABEL: Record<string, string> = {
  client: "출원인",
  client_contact: "담당자",
  opponent_agent: "대리인",
  inventor: "발명자",
};

function statusClass(status: string | null) {
  if (!status) return "bg-gray-100 text-gray-400";
  for (const [k, v] of Object.entries(STATUS_COLORS)) {
    if (status.includes(k)) return v;
  }
  return "bg-gray-100 text-gray-500";
}

export default function CasesPage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);

  const [viewTab, setViewTab] = useState<ViewTab>("cases");
  const [caseSearch, setCaseSearch] = useState("");
  const [caseSearchInput, setCaseSearchInput] = useState("");
  const [contactSearch, setContactSearch] = useState("");
  const [contactSearchInput, setContactSearchInput] = useState("");

  // 마감일 필터/정렬
  const [deadlineFilter, setDeadlineFilter] = useState<DeadlineFilter>("all");
  const [deadlineSort, setDeadlineSort] = useState<DeadlineSort>(null);

  // 업로드
  const [uploadType, setUploadType] = useState<UploadType>("cases");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [dragging, setDragging] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const { data: cases = [], isLoading: casesLoading } = useQuery({
    queryKey: ["cases", caseSearch],
    queryFn: () => caseApi.list(caseSearch || undefined),
  });

  const { data: contacts = [], isLoading: contactsLoading } = useQuery({
    queryKey: ["contacts", contactSearch],
    queryFn: () => caseApi.listContacts(contactSearch || undefined),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      uploadType === "contacts" ? caseApi.uploadContacts(file) : caseApi.uploadCases(file),
    onSuccess: (data) => {
      setUploadResult(data);
      setPendingFile(null);
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["contacts"] });
    },
  });

  const handleFileSelect = (file: File) => {
    setUploadResult(null);
    uploadMutation.reset();
    setPendingFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const clearFile = () => {
    setPendingFile(null);
    setUploadResult(null);
    uploadMutation.reset();
    if (fileRef.current) fileRef.current.value = "";
  };

  // 마감일 필터 + 정렬 적용
  const displayedCases = useMemo(() => {
    const now = new Date();
    const soon = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    let list = [...cases];

    if (deadlineFilter === "overdue") {
      list = list.filter((c) => c.deadline && new Date(c.deadline) < now);
    } else if (deadlineFilter === "soon") {
      list = list.filter((c) => c.deadline && new Date(c.deadline) >= now && new Date(c.deadline) <= soon);
    }

    if (deadlineSort) {
      list.sort((a, b) => {
        if (!a.deadline) return 1;
        if (!b.deadline) return -1;
        const diff = new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
        return deadlineSort === "asc" ? diff : -diff;
      });
    }

    return list;
  }, [cases, deadlineFilter, deadlineSort]);

  const overdueCount = cases.filter((c) => c.deadline && new Date(c.deadline) < new Date()).length;
  const soonCount = cases.filter((c) => {
    if (!c.deadline) return false;
    const d = new Date(c.deadline);
    const now = new Date();
    return d >= now && d <= new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
  }).length;

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* 헤더 */}
      <header className="flex shrink-0 items-center justify-between border-b bg-white px-6 py-3 shadow-sm">
        <h1 className="text-base font-bold text-gray-900">사건 / 고객 관리</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setShowUpload(!showUpload); clearFile(); }}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {showUpload ? "닫기" : "엑셀 업로드"}
          </button>
          <button
            onClick={caseApi.downloadTemplate}
            title="사건 DB 업로드용 엑셀 템플릿 (.xlsx)"
            className="rounded-md border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            템플릿 다운로드
          </button>
          <Link href="/" className="rounded-md border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
            인박스
          </Link>
        </div>
      </header>

      {/* 업로드 패널 */}
      {showUpload && (
        <div className="border-b bg-white px-6 py-4">
          <div className="mx-auto max-w-2xl space-y-3">
            <div className="flex gap-2">
              {(["cases", "contacts"] as UploadType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => { setUploadType(t); clearFile(); }}
                  className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                    uploadType === t ? "bg-blue-600 text-white" : "border text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {t === "cases" ? "사건 DB" : "고객 DB"}
                </button>
              ))}
            </div>

            <p className="text-xs text-gray-500">
              {uploadType === "cases"
                ? "필수 컬럼: OurRef (사건번호) · 자동 인식: 국문명칭, 의뢰인, 출원번호, 현재상태, 사건마감일 등"
                : "자동 인식: E-mail, 고객명, 고객구분, 회사명"}
            </p>

            {!pendingFile ? (
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed py-6 transition-colors ${
                  dragging ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
                }`}
              >
                <p className="text-sm font-medium text-gray-600">파일 선택 또는 드래그</p>
                <p className="text-xs text-gray-400 mt-0.5">.xlsx .xls 지원</p>
              </div>
            ) : (
              <div className="flex items-center justify-between rounded-lg border-2 border-blue-300 bg-blue-50 px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-gray-800">{pendingFile.name}</p>
                  <p className="text-xs text-gray-500">{(pendingFile.size / 1024).toFixed(1)} KB</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={clearFile} className="rounded border px-3 py-1.5 text-xs text-gray-500 hover:bg-white">취소</button>
                  <button
                    onClick={() => uploadMutation.mutate(pendingFile)}
                    disabled={uploadMutation.isPending}
                    className="rounded-lg bg-blue-600 px-5 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {uploadMutation.isPending ? "업로드 중..." : "업로드 시작"}
                  </button>
                </div>
              </div>
            )}

            <input ref={fileRef} type="file" accept=".xlsx,.xls" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); e.target.value = ""; }} />

            {uploadResult && (
              <div className="rounded-lg bg-green-50 p-3 text-sm">
                <span className="font-semibold text-green-800">완료 — </span>
                <span className="text-green-700">신규 {uploadResult.created}건 · 업데이트 {uploadResult.updated}건</span>
                {uploadResult.errors?.length > 0 && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs text-red-600">오류 {uploadResult.errors.length}건 보기</summary>
                    <div className="mt-1 space-y-0.5">
                      {uploadResult.errors.map((e: any, i: number) => (
                        <p key={i} className="text-xs text-red-500">{e.sheet} {e.row}행 ({e.ref}): {e.error}</p>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}

            {uploadMutation.isError && (
              <div className="rounded-lg bg-red-50 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-red-700">업로드 실패</p>
                  {pendingFile && (
                    <button
                      onClick={() => { uploadMutation.reset(); uploadMutation.mutate(pendingFile); }}
                      className="rounded bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700"
                    >
                      다시 시도
                    </button>
                  )}
                </div>
                <p className="text-xs mt-1 text-red-600">{(uploadMutation.error as any)?.response?.data?.detail || "서버 오류"}</p>
                <p className="text-xs text-red-400 mt-1">.xls 파일이면 Excel에서 .xlsx로 다시 저장 후 시도하세요.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 탭 + 본문 */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b bg-white px-6 py-2">
          <div className="flex gap-1">
            <button
              onClick={() => setViewTab("cases")}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                viewTab === "cases" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              사건 목록 {!casesLoading && <span className="ml-1 opacity-75">({cases.length})</span>}
            </button>
            <button
              onClick={() => setViewTab("contacts")}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                viewTab === "contacts" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              고객 / 연락처 {!contactsLoading && <span className="ml-1 opacity-75">({contacts.length})</span>}
            </button>
          </div>

          {viewTab === "cases" ? (
            <div className="flex items-center gap-2">
              {/* 마감일 필터 */}
              <div className="flex gap-1">
                {([
                  { v: "all" as DeadlineFilter, label: "전체" },
                  { v: "overdue" as DeadlineFilter, label: `초과 (${overdueCount})`, cls: "text-red-600" },
                  { v: "soon" as DeadlineFilter, label: `임박 (${soonCount})`, cls: "text-orange-600" },
                ]).map(({ v, label, cls }) => (
                  <button
                    key={v}
                    onClick={() => setDeadlineFilter(v === deadlineFilter ? "all" : v)}
                    className={`rounded px-2.5 py-1 text-xs font-medium transition-colors border ${
                      deadlineFilter === v
                        ? "bg-gray-800 text-white border-gray-800"
                        : `border-gray-200 hover:bg-gray-50 ${cls || "text-gray-600"}`
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {/* 마감일 정렬 */}
              <button
                onClick={() => setDeadlineSort((s) => s === "asc" ? "desc" : s === "desc" ? null : "asc")}
                className={`rounded px-2.5 py-1 text-xs font-medium border transition-colors ${
                  deadlineSort ? "bg-blue-600 text-white border-blue-600" : "border-gray-200 text-gray-600 hover:bg-gray-50"
                }`}
                title="마감일 정렬"
              >
                마감일 {deadlineSort === "asc" ? "↑" : deadlineSort === "desc" ? "↓" : "↕"}
              </button>
              <div className="flex items-center gap-1">
                <input
                  value={caseSearchInput}
                  onChange={(e) => setCaseSearchInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && setCaseSearch(caseSearchInput)}
                  placeholder="사건번호, 고객사, 명칭 검색..."
                  className="w-48 rounded border px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-300"
                />
                <button onClick={() => setCaseSearch(caseSearchInput)} className="rounded bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700">검색</button>
                {caseSearch && <button onClick={() => { setCaseSearch(""); setCaseSearchInput(""); }} className="text-xs text-gray-400 hover:text-gray-600">초기화</button>}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <input
                value={contactSearchInput}
                onChange={(e) => setContactSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && setContactSearch(contactSearchInput)}
                placeholder="이름, 이메일, 회사 검색..."
                className="w-56 rounded border px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
              <button onClick={() => setContactSearch(contactSearchInput)} className="rounded bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700">검색</button>
              {contactSearch && <button onClick={() => { setContactSearch(""); setContactSearchInput(""); }} className="text-xs text-gray-400 hover:text-gray-600">초기화</button>}
            </div>
          )}
        </div>

        {/* ── 사건 목록 ── */}
        {viewTab === "cases" && (
          <div className="flex-1 overflow-auto">
            {casesLoading ? (
              <div className="flex h-32 items-center justify-center text-gray-400">로딩 중...</div>
            ) : displayedCases.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-gray-400">
                {caseSearch || deadlineFilter !== "all" ? "조건에 맞는 사건이 없습니다." : "등록된 사건이 없습니다. 엑셀을 업로드해주세요."}
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-50 text-xs text-gray-500 shadow-sm">
                  <tr className="border-b">
                    <th className="px-4 py-2.5 text-left">사건번호</th>
                    <th className="px-4 py-2.5 text-left">국문명칭</th>
                    <th className="px-4 py-2.5 text-left">의뢰인</th>
                    <th className="px-4 py-2.5 text-left">출원번호</th>
                    <th className="px-4 py-2.5 text-left">국가</th>
                    <th className="px-4 py-2.5 text-left">권리</th>
                    <th className="px-4 py-2.5 text-left">담당</th>
                    <th className="px-4 py-2.5 text-left">
                      <span title="출원중·심사중·등록·거절 등">상태 ℹ</span>
                    </th>
                    <th
                      className="px-4 py-2.5 text-left cursor-pointer hover:text-blue-600 select-none"
                      onClick={() => setDeadlineSort((s) => s === "asc" ? "desc" : s === "desc" ? null : "asc")}
                    >
                      마감일 {deadlineSort === "asc" ? "↑" : deadlineSort === "desc" ? "↓" : ""}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {displayedCases.map((c: Case) => {
                    const now = new Date();
                    const deadline = c.deadline ? new Date(c.deadline) : null;
                    const isOverdue = deadline && deadline < now;
                    const isSoon = deadline && deadline >= now && deadline <= new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
                    return (
                      <tr key={c.id} className="border-b hover:bg-blue-50 transition-colors">
                        <td className="px-4 py-2 font-mono text-xs text-blue-700 whitespace-nowrap">{c.case_number}</td>
                        <td className="px-4 py-2 text-xs text-gray-700 max-w-[180px] truncate" title={c.title_ko ?? ""}>{c.title_ko || "-"}</td>
                        <td className="px-4 py-2 text-xs font-medium text-gray-900 whitespace-nowrap">{c.client_name}</td>
                        <td className="px-4 py-2 text-xs text-gray-500 whitespace-nowrap">{c.app_number || "-"}</td>
                        <td className="px-4 py-2 text-xs text-gray-500">{c.country}</td>
                        <td className="px-4 py-2 text-xs text-gray-500">{c.case_type || "-"}</td>
                        <td className="px-4 py-2 text-xs text-gray-500 whitespace-nowrap">{c.attorney || "-"}</td>
                        <td className="px-4 py-2">
                          {c.status && (
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusClass(c.status)}`}>
                              {c.status}
                            </span>
                          )}
                        </td>
                        <td className={`px-4 py-2 text-xs whitespace-nowrap font-medium ${
                          isOverdue ? "text-red-600" : isSoon ? "text-orange-500" : "text-gray-500"
                        }`}>
                          {c.deadline || "-"}
                          {isOverdue && <span className="ml-1 text-[9px] font-bold">초과</span>}
                          {isSoon && <span className="ml-1 text-[9px] font-bold">임박</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── 고객 / 연락처 목록 ── */}
        {viewTab === "contacts" && (
          <div className="flex-1 overflow-auto">
            {contactsLoading ? (
              <div className="flex h-32 items-center justify-center text-gray-400">로딩 중...</div>
            ) : contacts.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-gray-400">
                {contactSearch ? "검색 결과가 없습니다." : "등록된 연락처가 없습니다. 고객 DB 엑셀을 업로드해주세요."}
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-50 text-xs text-gray-500">
                  <tr className="border-b">
                    <th className="px-4 py-2.5 text-left">이름</th>
                    <th className="px-4 py-2.5 text-left">이메일</th>
                    <th className="px-4 py-2.5 text-left">회사</th>
                    <th className="px-4 py-2.5 text-left">구분</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts.map((c: Contact) => (
                    <tr key={c.id} className="border-b hover:bg-blue-50 transition-colors">
                      <td className="px-4 py-2 text-xs font-medium text-gray-900">{c.name || "-"}</td>
                      <td className="px-4 py-2 text-xs text-blue-600">
                        {c.email ? <a href={`mailto:${c.email}`} className="hover:underline">{c.email}</a> : "-"}
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-600">{c.org_name || "-"}</td>
                      <td className="px-4 py-2">
                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                          {ROLE_LABEL[c.role ?? ""] || c.role || "-"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
