import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CurrentUser {
  id: string;
  name: string;
  email: string;
  department: string | null;
  is_admin: boolean;
  personal_mailbox_connected: boolean;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

export function logout() {
  localStorage.removeItem("auth_token");
  window.location.href = "/login";
}

export function useAuth() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      setLoading(false);
      return;
    }

    axios
      .get<CurrentUser>(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((r) => setUser(r.data))
      .catch(() => {
        localStorage.removeItem("auth_token");
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  return { user, loading };
}
