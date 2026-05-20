import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockAgentFeed } from "@/lib/mock-data";

export default async function IncidentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <>
      <Header title={`Incident ${id}`} subtitle="Investigation timeline and remediation status" />
      <div className="grid grid-cols-3 gap-6 p-8">
        <div className="col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>High error rate on payment-api</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Badge variant="critical">critical</Badge>
                <Badge variant="high">investigating</Badge>
                <Badge variant="default">payment-api</Badge>
              </div>
              <p className="mt-4 text-muted-foreground">
                Database connection pool exhaustion from long-running analytics query.
                Confidence: 87%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Reasoning Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative space-y-0">
                {mockAgentFeed.map((trace, i) => (
                  <div key={trace.id} className="relative flex gap-4 pb-8">
                    <div className="flex flex-col items-center">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sentinel-cyan/20 text-sm font-bold text-sentinel-cyan">
                        {i + 1}
                      </div>
                      {i < mockAgentFeed.length - 1 && (
                        <div className="h-full w-px bg-border" />
                      )}
                    </div>
                    <div className="flex-1 rounded-lg border border-border/50 bg-secondary/30 p-4">
                      <div className="flex items-center justify-between">
                        <Badge variant="default">{trace.agent}</Badge>
                        <span className="text-xs text-muted-foreground">{trace.latency_ms}ms</span>
                      </div>
                      <p className="mt-2 font-medium">{trace.step}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{trace.reasoning}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Remediation Plan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="rounded-lg border border-border/50 p-3">
                <p className="font-medium">k8s_pod_restart</p>
                <p className="text-muted-foreground">namespace: production</p>
                <Badge variant="high" className="mt-2">Awaiting approval</Badge>
              </div>
              <div className="rounded-lg border border-border/50 p-3">
                <p className="font-medium">autoscale</p>
                <p className="text-muted-foreground">3 → 10 replicas</p>
                <Badge variant="low" className="mt-2">Auto-approved</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
