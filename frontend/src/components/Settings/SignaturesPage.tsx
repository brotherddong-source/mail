"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { signatureApi, SignatureItem, SignatureCreateBody } from "@/lib/api";
import Link from "next/link";

const LANG_OPTIONS = [
  { value: "ko", label: "국문" },
  { value: "en", label: "영문" },
];

const EMPTY_FORM: SignatureCreateBody = {
  sender_email: "",
  label: "",
  language: "ko",
  body: "",
  is_default: false,
};

export default function SignaturesPage() {
  const qc = useQueryClient();
  const [filterEmail, setFilterEmail] = useState("");
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<SignatureCreateBody>(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["signatures", filterEmail],
    queryFn: () => signatureApi.list(filterEmail || undefined),
  });
  const sigs = data?.signatures ?? [];

  const seedMutation = useMutation({
    mutationFn: signatureApi.seed,
    onSuccess: (d) => {
      qc.invalidateQueries({ queryKey: ["signatures"] });
      alert(`시드 완료: ${d.created}개 서명 등록됨`);
    },
  });

  const createMutation = useMutation({
    mutationFn: signatureApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["signatures"] });
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<SignatureCreateBody> }) =>
      signatureApi.update(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["signatures"] });
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: signatureApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["signatures"] }),
  });

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setShowForm(false);
  };

  const startEdit = (sig: SignatureItem) => {
    setForm({
      sender_email: sig.sender_email,
      label: sig.label,
      language: sig.language,
      body: sig.body,
      is_default: sig.is_default,
    });
    setEditId(sig.id);
    setShowForm(true);
  };

  const handleSubmit = () => {
    if (!form.sender_email || !form.label || !form.body) return;
    if (editId) {
      updateMutation.mutate({ id: editId, body: form });
    } else {
      createMutation.mutate(form);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">서명 관리</h1>
            <p className="text-sm text-gray-500">직원별 이메일 서명 등록 · 수정 · 삭제</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
              className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
            >
              {seedMutation.isPending ? "시드 중..." : "전체 직원 서명 자동 등록"}
            </button>
            <button
              onClick={() => { setShowForm(true); setEditId(null); setForm(EMPTY_FORM); }}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              + 서명 추가
            </button>
            <Link href="/" className="rounded-md border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
              인박스
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-6">

        {/* 서명 추가/수정 폼 */}
        {showForm && (
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-base font-semibold text-gray-800">
              {editId ? "서명 수정" : "새 서명 추가"}
            </h2>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600">발신자 이메일 *</label>
                  <input
                    type="email"
                    value={form.sender_email}
                    onChange={(e) => setForm({ ...form, sender_email: e.target.value })}
                    placeholder="jelee@ip-lab.co.kr"
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600">서명 레이블 *</label>
                  <input
                    type="text"
                    value={form.label}
                    onChange={(e) => setForm({ ...form, label: e.target.value })}
                    placeholder="이정은 주임 (국문)"
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  />
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600">언어</label>
                  <select
                    value={form.language}
                    onChange={(e) => setForm({ ...form, language: e.target.value as "ko" | "en" })}
                    className="rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  >
                    {LANG_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer mt-4">
                  <input
                    type="checkbox"
                    checked={form.is_default}
                    onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                    className="accent-blue-600"
                  />
                  기본 서명으로 설정
                </label>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600">서명 본문 *</label>
                <textarea
                  value={form.body}
                  onChange={(e) => setForm({ ...form, body: e.target.value })}
                  rows={10}
                  placeholder={"감사합니다.\n\n홍길동 변리사\n특허법인 아이피랩 특허1부\n서울 강서구 마곡동로 55, MARCUS 5층\nTEL: 02-6925-4821"}
                  className="w-full rounded border p-3 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-y font-mono"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleSubmit}
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {editId ? "저장" : "등록"}
                </button>
                <button onClick={resetForm} className="rounded-lg border px-6 py-2 text-sm text-gray-600 hover:bg-gray-50">
                  취소
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 필터 */}
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={filterEmail}
            onChange={(e) => setFilterEmail(e.target.value)}
            placeholder="이메일로 필터 (예: jelee@ip-lab.co.kr)"
            className="rounded border px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <span className="text-sm text-gray-500">총 {sigs.length}개</span>
        </div>

        {/* 서명 목록 */}
        {isLoading ? (
          <div className="flex h-24 items-center justify-center text-gray-400">로딩 중...</div>
        ) : sigs.length === 0 ? (
          <div className="rounded-xl border bg-white px-6 py-12 text-center text-gray-400">
            <p>등록된 서명이 없습니다.</p>
            <p className="mt-1 text-sm">"전체 직원 서명 자동 등록" 버튼을 눌러 27명의 서명을 한 번에 등록하세요.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sigs.map((sig) => (
              <div key={sig.id} className="rounded-xl border bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900">{sig.label}</span>
                      <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                        sig.language === "en" ? "bg-amber-100 text-amber-700" : "bg-green-100 text-green-700"
                      }`}>
                        {sig.language === "en" ? "영문" : "국문"}
                      </span>
                      {sig.is_default && (
                        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] text-blue-700">기본</span>
                      )}
                      <span className="text-xs text-gray-400 font-mono">{sig.sender_email}</span>
                    </div>
                    <pre className="mt-2 whitespace-pre-wrap text-xs text-gray-500 leading-relaxed line-clamp-4 max-h-20 overflow-hidden">
                      {sig.body}
                    </pre>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => startEdit(sig)}
                      className="rounded border px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                    >
                      수정
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`"${sig.label}" 서명을 삭제하시겠습니까?`)) {
                          deleteMutation.mutate(sig.id);
                        }
                      }}
                      className="rounded border border-red-200 px-3 py-1.5 text-xs text-red-500 hover:bg-red-50"
                    >
                      삭제
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
