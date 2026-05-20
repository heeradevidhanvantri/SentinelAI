import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockIncidents } from "@/lib/mock-data";
import Link from "next/link";

export default function IncidentsPage() {
  return (
    <>
      <Header title="Incidents" subtitle="AI-detected and operator-reported incidents" />
      <div className="p-8">
        <div className="mb-6 flex justify-end">
          <button className="rounded-lg bg-sentinel-cyan px-4 py-2 text-sm font-medium text-background hover:bg-sentinel-cyan/90">
            Trigger Investigation
          </button>
        </div>
        <div className="space-y-4">
          {mockIncidents.map((inc) => (
            <Link key={inc.id} href={`/incidents/${inc.id}`}>
              <Card className="transition-colors hover:border-sentinel-cyan/30">
                <CardContent className="flex items-center justify-between p-6">
                  <div>
                    <p className="text-lg font-medium">{inc.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {inc.service} · {inc.id} · {new Date(inc.created_at).toLocaleString()}
                    </p>
                    {inc.root_cause && (
                      <p className="mt-2 text-sm text-muted-foreground">
                        Root cause: {inc.root_cause}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={inc.severity}>{inc.severity}</Badge>
                    <Badge variant={inc.status === "resolved" ? "low" : "high"}>{inc.status}</Badge>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
