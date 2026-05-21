"use client";

import { Bell, Search, User, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";

export function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  const { logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-border/50 px-8">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            placeholder="Search incidents, services..."
            className="h-9 w-64 rounded-lg border border-border bg-secondary/50 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-sentinel-cyan"
          />
        </div>
        <button className="relative rounded-lg p-2 hover:bg-secondary">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-sentinel-red" />
        </button>
        <button
          onClick={logout}
          className="flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 hover:bg-secondary"
          title="Sign out"
        >
          <User className="h-4 w-4" />
          <span className="text-sm">Admin</span>
          <LogOut className="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      </div>
    </header>
  );
}
