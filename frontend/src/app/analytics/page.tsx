"use client";

import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";

const evalData = [
  { metric: "Hallucination Score", score: 0.89 },
  { metric: "Root Cause Accuracy", score: 0.87 },
  { metric: "Remediation Success", score: 0.94 },
  { metric: "Resolution Time", score: 0.82 },
];

const incidentTypes = [
  { name: "Database", value: 35, color: "#06b6d4" },
  { name: "Network", value: 25, color: "#3b82f6" },
  { name: "Deployment", value: 20, color: "#8b5cf6" },
  { name: "Resource", value: 20, color: "#f59e0b" },
];

export default function AnalyticsPage() {
  return (
    <>
      <Header title="Analytics" subtitle="AI evaluation metrics and incident trends" />
      <div className="grid grid-cols-2 gap-6 p-8">
        <Card>
          <CardHeader>
            <CardTitle>AI Evaluation Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={evalData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" domain={[0, 1]} stroke="#64748b" />
                <YAxis dataKey="metric" type="category" width={150} stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
                <Bar dataKey="score" fill="#06b6d4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Incident Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={incidentTypes} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                  {incidentTypes.map((e, i) => (
                    <Cell key={i} fill={e.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
