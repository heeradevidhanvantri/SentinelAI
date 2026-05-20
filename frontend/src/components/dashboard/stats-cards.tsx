import { AlertTriangle, Bot, Clock, CheckCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const stats = [
  { label: "Active Incidents", value: "3", change: "+1", icon: AlertTriangle, color: "text-sentinel-red" },
  { label: "Agents Running", value: "5", change: "100%", icon: Bot, color: "text-sentinel-cyan" },
  { label: "Avg Resolution", value: "12m", change: "-18%", icon: Clock, color: "text-sentinel-amber" },
  { label: "Remediation Rate", value: "94%", change: "+2%", icon: CheckCircle, color: "text-sentinel-green" },
];

export function StatsCards() {
  return (
    <div className="grid grid-cols-4 gap-4">
      {stats.map((s) => (
        <Card key={s.label}>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">{s.label}</p>
              <p className="mt-1 text-3xl font-bold">{s.value}</p>
              <p className="mt-1 text-xs text-sentinel-green">{s.change}</p>
            </div>
            <div className={`rounded-lg bg-secondary p-3 ${s.color}`}>
              <s.icon className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
