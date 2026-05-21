"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { api, ApiError } from "@/lib/api";
import type { Incident } from "@/lib/types";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getIncidents(1, 50);
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
    <>
      <Header title="Incidents" subtitle="AI-detected and operator-reported incidents" />
      <div className="p-8">
        {loading && (
          <div className="py-16">
            <LoadingSpinner label="Loading incidents..." />
          </div>
        )}

        {error && !loading && (
          <div className="mb-6 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && incidents.length === 0 && (
          <p className="py-16 text-center text-muted-foreground">
            No incidents found. Generate incidents via the API or demo scripts.
          </p>
        )}

        {!loading && !error && incidents.length > 0 && (
          <div className="space-y-4">
            {incidents.map((inc) => (
              <Link key={inc.id} href={`/incidents/${inc.id}`}>
                <Card className="transition-colors hover:border-sentinel-cyan/30">
                  <CardContent className="flex items-center justify-between p-6">
                    <div>
                      <p className="text-lg font-medium">{inc.title}</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {inc.service} · {inc.id} ·{" "}
                        {new Date(inc.created_at).toLocaleString()}
                      </p>
                      {inc.root_cause && (
                        <p className="mt-2 text-sm text-muted-foreground">
                          Root cause: {inc.root_cause}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={inc.severity}>{inc.severity}</Badge>
                      <Badge variant={inc.status === "resolved" ? "low" : "high"}>
                        {inc.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
