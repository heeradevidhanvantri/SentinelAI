import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, Search, Brain, Play, FileText } from "lucide-react";

const agents = [
  { name: "Monitoring", icon: Search, desc: "Metrics, logs, anomaly detection", status: "active", tasks: 1247 },
  { name: "Investigation", icon: Brain, desc: "Root-cause analysis with RAG", status: "active", tasks: 342 },
  { name: "Decision", icon: Bot, desc: "Remediation strategy selection", status: "active", tasks: 338 },
  { name: "Execution", icon: Play, desc: "Automated recovery actions", status: "active", tasks: 289 },
  { name: "Reporting", icon: FileText, desc: "Incident reports and post-mortems", status: "active", tasks: 301 },
];

export default function AgentsPage() {
  return (
    <>
      <Header title="AI Agents" subtitle="LangGraph multi-agent orchestration pipeline" />
      <div className="grid grid-cols-3 gap-6 p-8">
        {agents.map((a) => (
          <Card key={a.name}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-sentinel-cyan/20 p-2">
                    <a.icon className="h-5 w-5 text-sentinel-cyan" />
                  </div>
                  <CardTitle>{a.name}</CardTitle>
                </div>
                <Badge variant="healthy">{a.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{a.desc}</p>
              <p className="mt-4 text-2xl font-bold">{a.tasks.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">tasks processed (30d)</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
