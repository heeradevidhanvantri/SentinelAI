"use client";

import { useEffect, useState } from "react";
import { AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { api, ApiError } from "@/lib/api";
import type { HealthStatus } from "@/lib/types";

export function HealthPanel() {
  const [services, setServices] = useState<HealthStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getMonitoringHealth();
        if (!cancelled) setServices(data);
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError
              ? err.detail || err.message
              : "Failed to load health data";
          setError(message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

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
          services.map((svc) => (
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
