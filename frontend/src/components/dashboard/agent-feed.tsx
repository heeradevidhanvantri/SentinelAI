"use client";

import { useMemo } from "react";
import { Bot, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { api } from "@/lib/api";
import { useApiLoad } from "@/lib/use-api-load";
import type { AgentFeedItem } from "@/lib/types";

export function AgentFeed() {
  const load = useMemo(() => () => api.getAgentActivity(20).then((r) => r.feed), []);
  const { data: feed, loading, error } = useApiLoad<AgentFeedItem[]>(
    load,
    "Failed to load agent activity"
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-sentinel-cyan" />
          Agent Activity Feed
        </CardTitle>
      </CardHeader>
      <CardContent className="max-h-[400px] space-y-3 overflow-y-auto">
        {loading && <LoadingSpinner label="Loading agent feed..." className="py-6" />}

        {error && !loading && (
          <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && feed?.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No agent activity yet.
          </p>
        )}

        {!loading &&
          !error &&
          feed?.map((item) => (
            <div
              key={item.id}
              className="rounded-lg border border-border/50 bg-secondary/30 p-3"
            >
              <div className="flex items-center justify-between">
                <Badge variant="default">{item.agent}</Badge>
                <span className="text-xs text-muted-foreground">
                  {item.latency_ms != null ? `${item.latency_ms}ms` : "—"}
                </span>
              </div>
              <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
                {item.reasoning}
              </p>
              <p className="mt-1 text-xs text-muted-foreground/60">
                {item.step} · {item.incident_id}
              </p>
            </div>
          ))}
      </CardContent>
    </Card>
  );
}
