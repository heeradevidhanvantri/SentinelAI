import { Header } from "@/components/layout/header";
import { HealthPanel } from "@/components/dashboard/health-panel";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function InfrastructurePage() {
  return (
    <>
      <Header title="Infrastructure" subtitle="Service health, latency, and resource utilization" />
      <div className="grid grid-cols-2 gap-6 p-8">
        <HealthPanel />
        <Card>
          <CardHeader>
            <CardTitle>Observability Stack</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {[
              { name: "Prometheus", status: "Connected", url: "localhost:9090" },
              { name: "Grafana", status: "Connected", url: "localhost:3000" },
              { name: "OpenTelemetry", status: "Exporting", url: "localhost:4317" },
              { name: "Kafka", status: "Healthy", url: "localhost:9092" },
            ].map((s) => (
              <div key={s.name} className="flex justify-between rounded-lg border border-border/50 p-3">
                <span className="font-medium">{s.name}</span>
                <span className="text-sentinel-green">{s.status}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
