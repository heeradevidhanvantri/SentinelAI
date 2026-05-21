"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useAuth } from "@/contexts/auth-context";

const PUBLIC_PATHS = ["/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { loading, isAuthenticated } = useAuth();
  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    if (!loading && isAuthenticated && isPublic) {
      router.replace("/");
    }
  }, [loading, isAuthenticated, isPublic, router]);

  useEffect(() => {
    if (!loading && !isAuthenticated && !isPublic) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, isPublic, router]);

  if (isPublic) {
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner label="Loading session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner label="Redirecting to login..." />
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
