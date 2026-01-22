import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import MetricCard from "@/components/admin/MetricCard";
import { MessageSquare, Target, FileText, CheckCircle } from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const qualityCriteria = [
  { name: "Pertinence", score: 0.87 },
  { name: "Complétude", score: 0.82 },
  { name: "Concision", score: 0.91 },
  { name: "Précision", score: 0.85 },
  { name: "Cohérence", score: 0.88 },
];

const radarData = [
  { subject: "Pertinence", A: 87, fullMark: 100 },
  { subject: "Complétude", A: 82, fullMark: 100 },
  { subject: "Concision", A: 91, fullMark: 100 },
  { subject: "Précision", A: 85, fullMark: 100 },
  { subject: "Cohérence", A: 88, fullMark: 100 },
];

const distributionData = [
  { range: "0.0-0.2", count: 5 },
  { range: "0.2-0.4", count: 12 },
  { range: "0.4-0.6", count: 28 },
  { range: "0.6-0.8", count: 145 },
  { range: "0.8-1.0", count: 310 },
];

const AdminAnswerQuality = () => {
  const overallScore = 0.866;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-oswald font-medium tracking-tight">
          Qualité des Réponses
        </h1>
        <p className="text-muted-foreground">
          Analyse de la qualité des réponses générées par le système RAG
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Score Global"
          value={`${(overallScore * 100).toFixed(1)}%`}
          subtitle="Moyenne générale"
          icon={Target}
          variant="success"
        />
        <MetricCard
          title="Réponses Évaluées"
          value="500"
          subtitle="Dernières 24h"
          icon={MessageSquare}
        />
        <MetricCard
          title="Haute Qualité"
          value="62%"
          subtitle="Score > 0.8"
          icon={CheckCircle}
          variant="success"
        />
        <MetricCard
          title="À Améliorer"
          value="9%"
          subtitle="Score < 0.6"
          icon={FileText}
          variant="warning"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Quality Radar */}
        <Card>
          <CardHeader>
            <CardTitle>Scores par critère</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="hsl(var(--border))" />
                  <PolarAngleAxis
                    dataKey="subject"
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                  />
                  <Radar
                    name="Score"
                    dataKey="A"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary))"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Distribution des scores</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="range"
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
                  <Bar
                    dataKey="count"
                    name="Nombre de réponses"
                    fill="hsl(var(--primary))"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Criteria */}
      <Card>
        <CardHeader>
          <CardTitle>Détail par critère</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {qualityCriteria.map((criterion) => (
            <div key={criterion.name} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{criterion.name}</span>
                <span className="text-sm text-muted-foreground font-mono">
                  {(criterion.score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={criterion.score * 100} className="h-2" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminAnswerQuality;
