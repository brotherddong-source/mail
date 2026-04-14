import { Suspense } from "react";
import AuthContent from "./AuthContent";

export default function AuthPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-gray-400">로그인 처리 중...</div>}>
      <AuthContent />
    </Suspense>
  );
}
