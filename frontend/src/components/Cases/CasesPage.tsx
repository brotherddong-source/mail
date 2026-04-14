"use client";
import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { caseApi, Case } from "@/lib/api";
import Link from "next/link";

type UploadType = "contacts" | "cases";

export default function CasesPage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploadType, setUploadType] = useState<UploadType>("contacts");
  const [result, setResult] = useState<any>(null);
  const [dragging, setDragging] = useState(false);

  const { data: cases = [], isLoading } = useQuery({
    queryKey: ["cases"],
    queryFn: caseApi.list,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      uploadType === "contacts"
        ? caseApi.uploadContacts(file)
        : caseApi.uploadCases(file),
    onSuccess: (data) => {
      setResult(data);
      qc.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  const handleFile = (file: File) => {
    setResult(null);
    uploadMutation.mutate(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">사건 / 고객 관리</h1>
            <p className="text-sm text-gray-500">등록 사건 {cases.length}건</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={caseApi.downloadTemplate}
              className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              사건 템플릿 다운로드
            </button>
            <Link
              href="/"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              인박스로 이동
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-8">
        {/* 업로드 섹션 */}
        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-base font-semibold text-gray-800">엑셀 업로드</h2>

          {/* 업로드 타입 선택 */}
          <div className="mb-4 flex gap-2">
            <button
              onClick={() => setUploadType("contacts")}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                uploadType === "contacts"
                  ? "bg-blue-600 text-white"
                  : "border text-gray-600 hover:bg-gray-50"
              }`}
            >
              고객 DB 업로드
              <span className="ml-1.5 text-xs opacity-75">(연락처/이메일)</span>
            </button>
            <button
              onClick={() => setUploadType("cases")}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                uploadType === "cases"
                  ? "bg-blue-600 text-white"
                  : "border text-gray-600 hover:bg-gray-50"
              }`}
            >
              사건 DB 업로드
              <span className="ml-1.5 text-xs opacity-75">(사건번호/마감일)</span>
            </button>
          </div>

          {uploadType === "contacts" ? (
            <p className="mb-4 text-xs text-gray-500">
              특허사무소 고객 DB 형식(.xls/.xlsx) 지원 — E-mail, 고객명, 고객구분, 회사명 컬럼 자동 인식
            </p>
          ) : (
            <p className="mb-4 text-xs text-gray-500">
              필수 컬럼: 사건번호, 고객사명, 국가 / 선택: 출원번호, 사건유형, 상태, 마감일, 고객도메인
            </p>
          )}

          {/* 드래그 앤 드롭 영역 */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed py-10 transition-colors ${
              dragging ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
            }`}
          >
            <div className="text-4xl mb-3">📂</div>
            <p className="text-sm font-medium text-gray-700">
              엑셀 파일을 드래그하거나 클릭하여 선택
            </p>
            <p className="text-xs text-gray-400 mt-1">.xlsx, .xls 지원</p>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
                e.target.value = "";
              }}
            />
          </div>

          {/* 업로드 중 */}
          {uploadMutation.isPending && (
            <div className="mt-4 rounded-lg bg-blue-50 p-4 text-sm text-blue-700">
              업로드 중...
            </div>
          )}

          {/* 결과 */}
          {result && (
            <div className="mt-4 rounded-lg bg-green-50 p-4">
              <p className="text-sm font-semibold text-green-800 mb-2">업로드 완료</p>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded bg-white p-3 shadow-sm">
                  <div className="text-2xl font-bold text-green-600">{result.created}</div>
                  <div className="text-xs text-gray-500">신규 등록</div>
                </div>
                <div className="rounded bg-white p-3 shadow-sm">
                  <div className="text-2xl font-bold text-blue-600">{result.updated}</div>
                  <div className="text-xs text-gray-500">업데이트</div>
                </div>
                <div className="rounded bg-white p-3 shadow-sm">
                  <div className="text-2xl font-bold text-gray-500">{result.skipped ?? result.errors?.length ?? 0}</div>
                  <div className="text-xs text-gray-500">{result.skipped !== undefined ? "건너뜀" : "오류"}</div>
                </div>
              </div>
              {result.errors?.length > 0 && (
                <div className="mt-3 text-xs text-red-600">
                  오류: {result.errors.map((e: any) => `${e.row}행 (${e.error})`).join(", ")}
                </div>
              )}
            </div>
          )}

          {uploadMutation.isError && (
            <div className="mt-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">
              업로드 실패: {(uploadMutation.error as any)?.response?.data?.detail || "파일을 확인해주세요."}
            </div>
          )}
        </div>

        {/* 사건 목록 */}
        <div className="rounded-xl border bg-white shadow-sm">
          <div className="border-b px-6 py-4">
            <h2 className="text-base font-semibold text-gray-800">등록된 사건 목록</h2>
          </div>
          {isLoading ? (
            <div className="flex h-24 items-center justify-center text-gray-400">로딩 중...</div>
          ) : cases.length === 0 ? (
            <div className="flex h-24 items-center justify-center text-gray-400">
              등록된 사건이 없습니다. 엑셀을 업로드해주세요.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500">
                  <tr>
                    <th className="px-4 py-3 text-left">사건번호</th>
                    <th className="px-4 py-3 text-left">출원번호</th>
                    <th className="px-4 py-3 text-left">고객사</th>
                    <th className="px-4 py-3 text-left">국가</th>
                    <th className="px-4 py-3 text-left">유형</th>
                    <th className="px-4 py-3 text-left">상태</th>
                    <th className="px-4 py-3 text-left">마감일</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((c: Case) => (
                    <tr key={c.id} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-blue-700">{c.case_number}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{c.app_number || "-"}</td>
                      <td className="px-4 py-3 font-medium">{c.client_name}</td>
                      <td className="px-4 py-3">{c.country}</td>
                      <td className="px-4 py-3 text-gray-500">{c.case_type || "-"}</td>
                      <td className="px-4 py-3">
                        {c.status && (
                          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs">{c.status}</span>
                        )}
                      </td>
                      <td className={`px-4 py-3 text-xs ${
                        c.deadline && new Date(c.deadline) < new Date() ? "text-red-600 font-semibold" : "text-gray-500"
                      }`}>
                        {c.deadline || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
