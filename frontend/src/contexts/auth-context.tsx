"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { getToken, removeToken, setToken } from "@/lib/auth";
import { api, ApiError, formatApiError, login as apiLogin, setUnauthorizedHandler } from "@/lib/api";
import type { AuthUser } from "@/lib/types";

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function loadUser(token: string): Promise<AuthUser | null> {
  setToken(token);
  try {
    return await api.getMe();
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      removeToken();
      throw err;
    }
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function logout() {
    removeToken();
    setTokenState(null);
    setUser(null);
    router.push("/login");
  }

  useEffect(() => {
    async function restore() {
      const stored = getToken();
      if (!stored) {
        setLoading(false);
        return;
      }

      setTokenState(stored);
      try {
        setUser(await loadUser(stored));
      } catch {
        setTokenState(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    restore();

    setUnauthorizedHandler(() => {
      setTokenState(null);
      setUser(null);
      router.push("/login");
    });

    return () => setUnauthorizedHandler(null);
  }, [router]);

  async function login(email: string, password: string) {
    setError(null);
    try {
      const { access_token } = await apiLogin(email, password);
      setTokenState(access_token);
      setUser(await loadUser(access_token));
      router.push("/");
    } catch (err) {
      removeToken();
      setTokenState(null);
      setUser(null);
      setError(formatApiError(err, "Sign in failed. Please try again."));
      throw err;
    }
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        isAuthenticated: !!token,
        login,
        logout,
        error,
        clearError: () => setError(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
