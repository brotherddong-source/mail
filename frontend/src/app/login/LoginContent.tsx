"use client";
import { useSearchParams } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginContent() {
  const params = useSearchParams();
  const error = params.get("error");

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-2xl border bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <img src="/logo.png" alt="IPLAB" className="mx-auto mb-4 h-14 object-contain" />
          <p className="mt-1 text-sm text-gray-500">특허사무소 메일 자동화 시스템</p>
        </div>

        {error === "unauthorized" && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            접근 권한이 없습니다. 관리자에게 문의하세요.
          </div>
        )}
        {error === "inactive" && (
          <div className="mb-4 rounded-lg bg-yellow-50 p-3 text-sm text-yellow-700">
            계정이 비활성화되었습니다. 관리자에게 문의하세요.
          </div>
        )}

        <a
          href={`${API_URL}/auth/login`}
          className="flex w-full items-center justify-center gap-3 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50"
        >
          <svg width="20" height="20" viewBox="0 0 21 21" fill="none">
            <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
            <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
            <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
            <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
          </svg>
          Microsoft 계정으로 로그인
        </a>

        <p className="mt-6 text-center text-xs text-gray-400">
          ip-lab.co.kr 계정으로만 로그인 가능합니다
        </p>
      </div>
    </div>
  );
}
