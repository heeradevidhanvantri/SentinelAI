import { Header } from "@/components/layout/header";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { AgentFeed } from "@/components/dashboard/agent-feed";
import { IncidentList } from "@/components/dashboard/incident-list";
import { HealthPanel } from "@/components/dashboard/health-panel";

export default function DashboardPage() {
  return (
    <>
      <Header
        title="Operations Command Center"
        subtitle="Real-time AI SRE monitoring and incident response"
      />
      <div className="space-y-6 p-8">
        <StatsCards />
        <div className="grid grid-cols-3 gap-6">
          <MetricsChart />
          <AgentFeed />
        </div>
        <div className="grid grid-cols-2 gap-6">
          <IncidentList />
          <HealthPanel />
        </div>
      </div>
    </>
  );
}
