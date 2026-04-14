"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthCallback() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const token = params.get("token");
    const error = params.get("error");

    if (token) {
      localStorage.setItem("auth_token", token);
      router.replace("/");
    } else if (error === "unauthorized") {
      router.replace("/login?error=unauthorized");
    } else if (error === "inactive") {
      router.replace("/login?error=inactive");
    } else {
      router.replace("/login");
    }
  }, [params, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="text-4xl mb-4">⏳</div>
        <p className="text-gray-600">로그인 처리 중...</p>
      </div>
    </div>
  );
}
