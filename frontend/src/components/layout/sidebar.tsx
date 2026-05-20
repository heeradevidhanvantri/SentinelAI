"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertTriangle,
  Bot,
  Server,
  BarChart3,
  Shield,
  Settings,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/incidents", label: "Incidents", icon: AlertTriangle },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/infrastructure", label: "Infrastructure", icon: Server },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/approvals", label: "Approvals", icon: Shield },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border/50 bg-card/40 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-2 border-b border-border/50 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sentinel-cyan/20">
          <Zap className="h-5 w-5 text-sentinel-cyan" />
        </div>
        <div>
          <span className="font-bold tracking-tight">SentinelAI</span>
          <p className="text-[10px] text-muted-foreground">AI SRE Platform</p>
        </div>
      </div>
      <nav className="space-y-1 p-4">
        {nav.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all",
                active
                  ? "bg-sentinel-cyan/10 text-sentinel-cyan"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="absolute bottom-4 left-4 right-4 rounded-lg border border-border/50 bg-secondary/50 p-3">
        <p className="text-xs font-medium">System Status</p>
        <div className="mt-1 flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-sentinel-green" />
          <span className="text-xs text-muted-foreground">5 agents active</span>
        </div>
      </div>
    </aside>
  );
}
