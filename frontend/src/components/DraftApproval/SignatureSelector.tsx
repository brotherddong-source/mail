"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { mailApi, SignatureItem } from "@/lib/api";

interface Props {
  senderEmail: string;
  selectedId: string | null;
  currentLang: "ko" | "en";
  onSelect: (sig: SignatureItem) => void;
}

export default function SignatureSelector({ senderEmail, selectedId, currentLang, onSelect }: Props) {
  const [preview, setPreview] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["signatures", senderEmail],
    queryFn: () => mailApi.listSignatures(senderEmail),
    enabled: !!senderEmail,
  });

  if (isLoading) return <div className="text-xs text-gray-400">서명 로딩 중...</div>;
  if (!data?.signatures?.length) return null;

  const sigs = data.signatures;
  // 현재 언어에 맞는 서명 우선 표시
  const sorted = [...sigs].sort((a, b) => {
    if (a.language === currentLang && b.language !== currentLang) return -1;
    if (b.language === currentLang && a.language !== currentLang) return 1;
    if (a.is_default && !b.is_default) return -1;
    if (b.is_default && !a.is_default) return 1;
    return 0;
  });

  const selected = sigs.find((s) => s.id === selectedId) ?? sorted[0];

  return (
    <div className="rounded-lg border bg-gray-50 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-600">서명 선택</span>
        <button
          onClick={() => setPreview(!preview)}
          className="text-[10px] text-blue-500 hover:text-blue-700"
        >
          {preview ? "미리보기 닫기" : "미리보기"}
        </button>
      </div>

      <div className="flex flex-col gap-1">
        {sorted.map((sig) => (
          <label
            key={sig.id}
            className={`flex cursor-pointer items-center gap-2 rounded-md border px-2.5 py-2 transition-all ${
              selected?.id === sig.id
                ? "border-blue-500 bg-blue-50"
                : "border-gray-200 bg-white hover:border-blue-200"
            }`}
          >
            <input
              type="radio"
              name="signature"
              value={sig.id}
              checked={selected?.id === sig.id}
              onChange={() => onSelect(sig)}
              className="accent-blue-600"
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-800 truncate">{sig.label}</p>
            </div>
            <span
              className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-semibold ${
                sig.language === "en"
                  ? "bg-amber-100 text-amber-700"
                  : "bg-green-100 text-green-700"
              }`}
            >
              {sig.language === "en" ? "영문" : "국문"}
            </span>
            {sig.is_default && (
              <span className="shrink-0 rounded bg-gray-100 px-1 py-0.5 text-[9px] text-gray-500">
                기본
              </span>
            )}
          </label>
        ))}
      </div>

      {preview && selected && (
        <div className="mt-2 rounded border bg-white p-2">
          <p className="mb-1 text-[10px] font-semibold text-gray-400">서명 미리보기</p>
          <pre className="whitespace-pre-wrap text-[10px] text-gray-600 leading-relaxed">
            {selected.body}
          </pre>
        </div>
      )}
    </div>
  );
}
