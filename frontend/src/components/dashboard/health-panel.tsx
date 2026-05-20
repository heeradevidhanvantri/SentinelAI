import { Server } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockHealth } from "@/lib/mock-data";

export function HealthPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5 text-sentinel-blue" />
          Infrastructure Health
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {mockHealth.map((s) => (
          <div key={s.service} className="flex items-center justify-between rounded-lg border border-border/50 p-3">
            <div>
              <p className="font-medium">{s.service}</p>
              <p className="text-xs text-muted-foreground">
                {s.latency_ms}ms · {s.error_rate}% errors · CPU {s.cpu_percent}%
              </p>
            </div>
            <Badge variant={s.status}>{s.status}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
