"use client";

import { useMemo } from "react";
import { AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { api } from "@/lib/api";
import { useApiLoad } from "@/lib/use-api-load";
import type { HealthStatus } from "@/lib/types";

export function HealthPanel() {
  const load = useMemo(() => () => api.getMonitoringHealth(), []);
  const { data: services, loading, error } = useApiLoad<HealthStatus[]>(
    load,
    "Failed to load health data"
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Service Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading && <LoadingSpinner label="Loading health status..." className="py-6" />}

        {error && !loading && (
          <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading &&
          !error &&
          services?.map((svc) => (
            <div
              key={svc.service}
              className="flex items-center justify-between rounded-lg border border-border/50 bg-secondary/30 p-3"
            >
              <div>
                <p className="font-medium">{svc.service}</p>
                <p className="text-xs text-muted-foreground">
                  {svc.latency_ms}ms · {svc.error_rate}% errors
                </p>
              </div>
              <Badge variant={svc.status}>{svc.status}</Badge>
            </div>
          ))}
      </CardContent>
    </Card>
  );
}
