import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <>
      <Header title="Settings" subtitle="Platform configuration and integrations" />
      <div className="max-w-2xl space-y-6 p-8">
        <Card>
          <CardHeader><CardTitle>API Configuration</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">API URL</label>
              <input
                className="mt-1 w-full rounded-lg border border-border bg-secondary/50 px-3 py-2 text-sm"
                defaultValue={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                readOnly
              />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Integrations</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            {["OpenAI", "Pinecone", "Prometheus", "Kubernetes", "AWS ECS"].map((i) => (
              <div key={i} className="flex justify-between rounded-lg border border-border/50 p-3">
                <span>{i}</span>
                <span className="text-muted-foreground">Configure in .env</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
