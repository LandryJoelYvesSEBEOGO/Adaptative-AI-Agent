import {
  Server,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  Activity,
} from "lucide-react";
import MetricCard from "@/components/admin/MetricCard";
import RequestsChart from "@/components/admin/RequestsChart";
import RecentActivity from "@/components/admin/RecentActivity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { cn } from "@/lib/utils";

// Mock data
const chartData = [
  { date: "16 Dec", requests: 145, success: 138, errors: 7 },
  { date: "17 Dec", requests: 168, success: 160, errors: 8 },
  { date: "18 Dec", requests: 189, success: 182, errors: 7 },
  { date: "19 Dec", requests: 201, success: 195, errors: 6 },
  { date: "20 Dec", requests: 178, success: 170, errors: 8 },
  { date: "21 Dec", requests: 156, success: 149, errors: 7 },
  { date: "22 Dec", requests: 134, success: 128, errors: 6 },
];

const errorDistribution = [
  { name: "Timeout", value: 35, color: "hsl(var(--destructive))" },
  { name: "Erreur LLM", value: 25, color: "hsl(var(--warning))" },
  { name: "Retrieval", value: 20, color: "hsl(var(--chart-3))" },
  { name: "Web Search", value: 15, color: "hsl(var(--chart-4))" },
  { name: "Autres", value: 5, color: "hsl(var(--muted-foreground))" },
];

const recentRequests = [
  {
    id: "1",
    timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
    user: "jean.dupont@company.com",
    question: "Comment puis-je configurer les paramètres de sécurité ?",
    status: "success" as const,
    latency: 2.34,
  },
  {
    id: "2",
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    user: "marie.martin@company.com",
    question: "Quelles sont les meilleures pratiques pour l'intégration API ?",
    status: "success" as const,
    latency: 1.89,
  },
  {
    id: "3",
    timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
    user: "pierre.bernard@company.com",
    question: "Pouvez-vous m'expliquer le processus de déploiement ?",
    status: "error" as const,
    latency: 8.45,
  },
  {
    id: "4",
    timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
    user: "sophie.petit@company.com",
    question: "Comment générer un rapport d'activité mensuel ?",
    status: "success" as const,
    latency: 3.12,
  },
  {
    id: "5",
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    user: "lucas.moreau@company.com",
    question: "Quels sont les prérequis pour utiliser le module avancé ?",
    status: "success" as const,
    latency: 2.67,
  },
];

const AdminDashboard = () => {
  return (
    <div className="space-y-6 relative">
      {/* Header with gradient effect */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-transparent blur-3xl opacity-50" />
        <div className="relative flex flex-col gap-1">
          <h1 className="text-4xl md:text-5xl font-oswald font-medium tracking-tight">
            Dashboard
          </h1>
          <p className="text-muted-foreground text-lg">
            Vue d'ensemble des performances du système RAG
          </p>
        </div>
      </div>

      {/* Metrics Grid with enhanced cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Requêtes"
          value="12,847"
          subtitle="Toutes les requêtes"
          icon={Server}
          trend={{ value: 12.5, isPositive: true }}
        />
        <MetricCard
          title="Requêtes Aujourd'hui"
          value="134"
          subtitle="Depuis minuit"
          icon={Activity}
          trend={{ value: 8.2, isPositive: true }}
          variant="success"
        />
        <MetricCard
          title="Taux de Succès"
          value="96.2%"
          subtitle="5 échecs aujourd'hui"
          icon={CheckCircle2}
          variant="success"
        />
        <MetricCard
          title="Latence Moyenne"
          value="2.4s"
          subtitle="End-to-end"
          icon={Clock}
          trend={{ value: 5.3, isPositive: false }}
          variant="warning"
        />
      </div>

      {/* Charts Row with enhanced styling */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <RequestsChart data={chartData} />
        </div>
        
        {/* Error Distribution with enhanced card */}
        <Card className="relative overflow-hidden border-border/50 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-2xl" />
          <CardHeader className="pb-2 relative z-10">
            <CardTitle className="text-lg font-oswald">Répartition des erreurs</CardTitle>
          </CardHeader>
          <CardContent className="relative z-10">
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={errorDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {errorDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "8px",
                      boxShadow: "0 4px 20px -2px hsl(var(--foreground) / 0.08)",
                    }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: "12px" }}
                    formatter={(value) => (
                      <span style={{ color: "hsl(var(--foreground))" }}>{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity with enhanced styling */}
      <div className="relative">
        <RecentActivity requests={recentRequests} />
      </div>

      {/* System Status with template-inspired design */}
      <Card className="relative overflow-hidden bg-gradient-to-br from-foreground to-foreground/95 text-background border-0 shadow-xl">
        <div className="absolute inset-0 opacity-10">
          <div 
            className="absolute inset-0"
            style={{
              backgroundImage: "url('https://grainy-gradients.vercel.app/noise.svg')",
            }}
          />
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-3xl" />
        <CardContent className="p-6 relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <span className="text-xs font-space uppercase tracking-widest text-primary mb-2 block">
                État du Système
              </span>
              <h3 className="text-xl font-oswald font-medium">Statut en temps réel</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
              <span className="text-sm font-medium">Opérationnel</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-sm">
            <div className="flex justify-between items-center p-3 rounded-lg bg-background/10 backdrop-blur-sm border border-background/20">
              <span className="text-muted-foreground">&gt; RAG Pipeline</span>
              <span className="text-success font-semibold">Active</span>
            </div>
            <div className="flex justify-between items-center p-3 rounded-lg bg-background/10 backdrop-blur-sm border border-background/20">
              <span className="text-muted-foreground">&gt; Vector DB</span>
              <span className="text-success font-semibold">Connected</span>
            </div>
            <div className="flex justify-between items-center p-3 rounded-lg bg-background/10 backdrop-blur-sm border border-background/20">
              <span className="text-muted-foreground">&gt; LLM Status</span>
              <span className="text-success font-semibold">98.5% Uptime</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="relative overflow-hidden border-border/50 hover:border-primary/30 transition-all duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-success/10 rounded-full blur-2xl" />
          <CardHeader className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-success" />
              <CardTitle className="text-lg font-oswald">Tendances</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="relative z-10">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Croissance hebdomadaire</span>
                <span className="text-lg font-oswald font-medium text-success">+12.5%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Utilisateurs actifs</span>
                <span className="text-lg font-oswald font-medium">+8.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Satisfaction moyenne</span>
                <span className="text-lg font-oswald font-medium text-success">4.8/5</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden border-border/50 hover:border-primary/30 transition-all duration-300">
          <div className="absolute top-0 right-0 w-24 h-24 bg-warning/10 rounded-full blur-2xl" />
          <CardHeader className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-warning" />
              <CardTitle className="text-lg font-oswald">Alertes</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="relative z-10">
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-warning/5 border border-warning/20">
                <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Latence P95 élevée</p>
                  <p className="text-xs text-muted-foreground mt-1">4.2s (seuil: 3.5s)</p>
                </div>
              </div>
              <div className="text-sm text-muted-foreground text-center py-2">
                Aucune autre alerte active
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
