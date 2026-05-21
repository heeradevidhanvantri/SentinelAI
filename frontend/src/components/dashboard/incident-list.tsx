"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { api, ApiError } from "@/lib/api";
import type { Incident } from "@/lib/types";

export function IncidentList() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getIncidents(1, 10);
        if (!cancelled) setIncidents(data.items);
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError
              ? err.detail || err.message
              : "Failed to load incidents";
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
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Live Incidents</CardTitle>
        <Link href="/incidents" className="text-sm text-sentinel-cyan hover:underline">
          View all
        </Link>
      </CardHeader>
      <CardContent>
        {loading && <LoadingSpinner label="Loading incidents..." className="py-8" />}

        {error && !loading && (
          <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && incidents.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No incidents yet. Trigger an investigation or generate synthetic incidents.
          </p>
        )}

        {!loading && !error && incidents.length > 0 && (
          <div className="space-y-3">
            {incidents.map((inc) => (
              <Link
                key={inc.id}
                href={`/incidents/${inc.id}`}
                className="block rounded-lg border border-border/50 bg-secondary/30 p-4 transition-colors hover:border-sentinel-cyan/30"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{inc.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{inc.service}</p>
                  </div>
                  <Badge variant={inc.severity}>{inc.severity}</Badge>
                </div>
                <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                  <Badge variant={inc.status === "resolved" ? "low" : "medium"}>
                    {inc.status}
                  </Badge>
                  {inc.root_cause_confidence != null && (
                    <span>
                      RC confidence: {(inc.root_cause_confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
