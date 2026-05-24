"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useAuth } from "@/contexts/auth-context";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { loading, isAuthenticated } = useAuth();
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (loading) return;
    if (isAuthenticated && isLogin) router.replace("/");
    else if (!isAuthenticated && !isLogin) router.replace("/login");
  }, [loading, isAuthenticated, isLogin, router]);

  if (isLogin) {
    return <>{children}</>;
  }

  if (loading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  return (
    <>
      <Sidebar />
      <main className="ml-64 min-h-screen">{children}</main>
    </>
  );
}
