import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockIncidents } from "@/lib/mock-data";

export function IncidentList() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Live Incidents</CardTitle>
        <Link href="/incidents" className="text-sm text-sentinel-cyan hover:underline">
          View all
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {mockIncidents.map((inc) => (
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
              <Badge variant={inc.status === "resolved" ? "low" : "medium"}>{inc.status}</Badge>
              {inc.root_cause_confidence && (
                <span>RC confidence: {(inc.root_cause_confidence * 100).toFixed(0)}%</span>
              )}
            </div>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
