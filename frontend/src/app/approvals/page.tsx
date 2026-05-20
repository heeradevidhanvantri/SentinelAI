"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { pendingApprovals } from "@/lib/mock-data";

export default function ApprovalsPage() {
  return (
    <>
      <Header title="Remediation Approvals" subtitle="Human-in-the-loop for production actions" />
      <div className="p-8 space-y-4">
        {pendingApprovals.map((a) => (
          <Card key={a.id}>
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <p className="font-medium">{a.action_type}</p>
                <p className="text-sm text-muted-foreground">
                  Incident: {a.incident_id} · {JSON.stringify(a.parameters)}
                </p>
              </div>
              <div className="flex gap-3">
                <button className="rounded-lg border border-border px-4 py-2 text-sm hover:bg-secondary">
                  Reject
                </button>
                <button className="rounded-lg bg-sentinel-green px-4 py-2 text-sm font-medium text-background">
                  Approve
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
        {pendingApprovals.length === 0 && (
          <p className="text-center text-muted-foreground">No pending approvals</p>
        )}
      </div>
    </>
  );
}
