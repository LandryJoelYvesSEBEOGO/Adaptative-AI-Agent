import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Clock, User, Zap } from "lucide-react";

interface RecentRequest {
  id: string;
  timestamp: string;
  user: string;
  question: string;
  status: "success" | "error";
  latency: number;
}

interface RecentActivityProps {
  requests: RecentRequest[];
}

const RecentActivity = ({ requests }: RecentActivityProps) => {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "À l'instant";
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffMins < 1440) return `Il y a ${Math.floor(diffMins / 60)}h`;
    return date.toLocaleDateString("fr-FR");
  };

  return (
    <Card className="relative overflow-hidden border-border/50 hover:border-primary/30 transition-all duration-300">
      {/* Background gradient effect */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-primary/5 rounded-full blur-3xl" />
      
      <CardHeader className="pb-3 relative z-10">
        <CardTitle className="text-lg font-oswald">Activité récente</CardTitle>
        <p className="text-sm text-muted-foreground mt-1">10 dernières requêtes</p>
      </CardHeader>
      <CardContent className="p-0 relative z-10">
        <div className="divide-y divide-border">
          {requests.map((request, index) => (
            <div
              key={request.id}
              className={cn(
                "px-6 py-4 hover:bg-muted/50 transition-colors cursor-pointer group",
                index === 0 && "bg-muted/30"
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3">
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 transition-colors",
                      request.status === "success" 
                        ? "bg-success/10 group-hover:bg-success/20" 
                        : "bg-destructive/10 group-hover:bg-destructive/20"
                    )}>
                      {request.status === "success" ? (
                        <Zap className="w-4 h-4 text-success" />
                      ) : (
                        <Clock className="w-4 h-4 text-destructive" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium leading-relaxed group-hover:text-primary transition-colors">
                        {request.question}
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          <span className="truncate max-w-[200px]">{request.user}</span>
                        </div>
                        <span>•</span>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatTimestamp(request.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge
                    variant={request.status === "success" ? "default" : "destructive"}
                    className={cn(
                      "text-xs font-medium",
                      request.status === "success" && "bg-success hover:bg-success/90 text-success-foreground"
                    )}
                  >
                    {request.status === "success" ? "Succès" : "Échec"}
                  </Badge>
                  <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-muted/50">
                    <Zap className="w-3 h-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground font-mono font-medium">
                      {request.latency.toFixed(2)}s
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default RecentActivity;
