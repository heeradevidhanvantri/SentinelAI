import { Bot } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockAgentFeed } from "@/lib/mock-data";

export function AgentFeed() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-sentinel-cyan" />
          Agent Activity Feed
        </CardTitle>
      </CardHeader>
      <CardContent className="max-h-[400px] space-y-3 overflow-y-auto">
        {mockAgentFeed.map((item) => (
          <div key={item.id} className="rounded-lg border border-border/50 bg-secondary/30 p-3">
            <div className="flex items-center justify-between">
              <Badge variant="default">{item.agent}</Badge>
              <span className="text-xs text-muted-foreground">{item.latency_ms}ms</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground line-clamp-2">{item.reasoning}</p>
            <p className="mt-1 text-xs text-muted-foreground/60">{item.step} · {item.incident_id}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
