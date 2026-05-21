"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { getToken, removeToken, setToken } from "@/lib/auth";
import { login as apiLogin, setUnauthorizedHandler } from "@/lib/api";

interface AuthContextValue {
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    removeToken();
    setTokenState(null);
    router.push("/login");
  }, [router]);

  useEffect(() => {
    setTokenState(getToken());
    setLoading(false);

    setUnauthorizedHandler(() => {
      setTokenState(null);
      router.push("/login");
    });

    return () => setUnauthorizedHandler(null);
  }, [router]);

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null);
      try {
        const response = await apiLogin(email, password);

        if (!response.access_token) {
          throw new Error("Login response did not include access_token");
        }

        setToken(response.access_token);
        setTokenState(response.access_token);
        console.info("[auth] token stored", {
          expires_in: response.expires_in,
          token_type: response.token_type,
        });
        router.push("/");
      } catch (err) {
        console.error("[auth] login failed in context", err);
        const message =
          err instanceof Error ? err.message : "Login failed. Please try again.";
        setError(message);
        throw err;
      }
    },
    [router]
  );

  const value = useMemo(
    () => ({
      token,
      loading,
      isAuthenticated: !!token,
      login,
      logout,
      error,
      clearError: () => setError(null),
    }),
    [token, loading, login, logout, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
