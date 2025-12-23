import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Clock, Database, Search } from "lucide-react";
import MetricCard from "@/components/admin/MetricCard";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from "recharts";

const latencyData = [
  { name: "End-to-End", avg: 2.4, p95: 4.2, p99: 6.8 },
  { name: "Retrieval", avg: 0.8, p95: 1.5, p99: 2.1 },
  { name: "Generation", avg: 1.2, p95: 2.3, p99: 3.5 },
  { name: "Grading", avg: 0.3, p95: 0.6, p99: 0.9 },
  { name: "Web Search", avg: 0.5, p95: 1.0, p99: 1.8 },
];

const latencyTrend = [
  { date: "16 Dec", endToEnd: 2.2, retrieval: 0.7, generation: 1.1 },
  { date: "17 Dec", endToEnd: 2.5, retrieval: 0.9, generation: 1.3 },
  { date: "18 Dec", endToEnd: 2.3, retrieval: 0.8, generation: 1.2 },
  { date: "19 Dec", endToEnd: 2.6, retrieval: 0.8, generation: 1.4 },
  { date: "20 Dec", endToEnd: 2.4, retrieval: 0.7, generation: 1.2 },
  { date: "21 Dec", endToEnd: 2.1, retrieval: 0.6, generation: 1.0 },
  { date: "22 Dec", endToEnd: 2.4, retrieval: 0.8, generation: 1.2 },
];

const AdminMetrics = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-oswald font-medium tracking-tight">
          Métriques & Performance
        </h1>
        <p className="text-muted-foreground">
          Analyse détaillée des latences et performances du système
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Latence Moyenne"
          value="2.4s"
          subtitle="End-to-end"
          icon={Clock}
        />
        <MetricCard
          title="P95 Latence"
          value="4.2s"
          subtitle="95e percentile"
          icon={Activity}
          variant="warning"
        />
        <MetricCard
          title="Precision@5"
          value="87.3%"
          subtitle="Retrieval accuracy"
          icon={Database}
          variant="success"
        />
        <MetricCard
          title="MAP Score"
          value="0.82"
          subtitle="Mean Avg Precision"
          icon={Search}
          variant="success"
        />
      </div>

      {/* Latency by Component */}
      <Card>
        <CardHeader>
          <CardTitle>Latence par composant</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  type="number"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                  width={100}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    borderColor: "hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
                <Bar dataKey="avg" name="Moyenne" fill="hsl(var(--primary))" radius={4} />
                <Bar dataKey="p95" name="P95" fill="hsl(var(--warning))" radius={4} />
                <Bar dataKey="p99" name="P99" fill="hsl(var(--destructive))" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Latency Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Évolution des latences (7 jours)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={latencyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  axisLine={{ stroke: "hsl(var(--border))" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    borderColor: "hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="endToEnd"
                  name="End-to-End"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="retrieval"
                  name="Retrieval"
                  stroke="hsl(var(--success))"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="generation"
                  name="Generation"
                  stroke="hsl(var(--chart-3))"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminMetrics;
