"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { mailApi, TemplateItem } from "@/lib/api";

const CATEGORY_LABEL: Record<string, string> = {
  acknowledge: "수신 확인",
  filing_instruction: "출원 지시",
  filing_complete: "출원 완료보고",
  oa_complete: "OA 완료보고",
  revision: "리비전",
  reminder: "리마인더",
  kipo_notice: "특허청 통지",
  drawing_request: "도면 의뢰",
  new_case: "사건수임",
  gpoa: "GPOA/위임장",
};

const LANG_BADGE: Record<string, string> = {
  ko: "국문",
  en: "영문",
};

interface Props {
  mailId: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function TemplateSelector({ mailId, selectedId, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["templates", mailId],
    queryFn: () => mailApi.listTemplates(mailId),
  });

  if (isLoading) return <div className="text-xs text-gray-400 py-2">템플릿 로딩 중...</div>;
  if (!data) return null;

  const { templates, recommended_id } = data;
  const recommended = templates.find((t) => t.is_recommended);
  const visible = expanded ? templates : templates.slice(0, 4);

  return (
    <div className="rounded-lg border bg-gray-50 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-600">초안 유형 선택</span>
        {recommended && (
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">
            AI 추천: {recommended.name}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        {visible.map((tpl) => (
          <TemplateCard
            key={tpl.id}
            tpl={tpl}
            selected={selectedId === tpl.id}
            onSelect={onSelect}
          />
        ))}
      </div>

      {templates.length > 4 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 w-full text-center text-xs text-blue-500 hover:text-blue-700"
        >
          {expanded ? "접기 ▲" : `전체 보기 (${templates.length}개) ▼`}
        </button>
      )}

      {selectedId && (
        <div className="mt-2 rounded bg-white border px-2 py-1.5">
          <p className="text-[10px] text-gray-500">
            선택됨:{" "}
            <span className="font-medium text-gray-700">
              {templates.find((t) => t.id === selectedId)?.name}
            </span>
            {" — "}
            <span>{templates.find((t) => t.id === selectedId)?.use_case}</span>
          </p>
        </div>
      )}
    </div>
  );
}

function TemplateCard({
  tpl,
  selected,
  onSelect,
}: {
  tpl: TemplateItem;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      onClick={() => onSelect(tpl.id)}
      className={`relative rounded-lg border p-2 text-left transition-all ${
        selected
          ? "border-blue-500 bg-blue-50 ring-1 ring-blue-400"
          : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50"
      }`}
    >
      {tpl.is_recommended && (
        <span className="absolute right-1 top-1 rounded-full bg-blue-500 px-1 py-0.5 text-[9px] font-bold text-white">
          추천
        </span>
      )}
      <p className="pr-6 text-[11px] font-semibold text-gray-800 leading-tight">{tpl.name}</p>
      <div className="mt-1 flex items-center gap-1">
        <span className="rounded bg-gray-100 px-1 py-0.5 text-[9px] text-gray-500">
          {CATEGORY_LABEL[tpl.category] ?? tpl.category}
        </span>
        <span
          className={`rounded px-1 py-0.5 text-[9px] font-medium ${
            tpl.language === "en"
              ? "bg-amber-100 text-amber-700"
              : "bg-green-100 text-green-700"
          }`}
        >
          {LANG_BADGE[tpl.language]}
        </span>
      </div>
    </button>
  );
}
