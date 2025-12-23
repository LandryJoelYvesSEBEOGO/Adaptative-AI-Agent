import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: "default" | "success" | "warning" | "destructive";
}

const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = "default",
}: MetricCardProps) => {
  const variantStyles = {
    default: "text-primary",
    success: "text-success",
    warning: "text-warning",
    destructive: "text-destructive",
  };

  const iconBgStyles = {
    default: "bg-primary/10 dark:bg-primary/20",
    success: "bg-success/10 dark:bg-success/20",
    warning: "bg-warning/10 dark:bg-warning/20",
    destructive: "bg-destructive/10 dark:bg-destructive/20",
  };

  return (
    <Card className="relative overflow-hidden border-border/50 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5 group">
      {/* Background gradient effect */}
      <div className={cn(
        "absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl opacity-50 group-hover:opacity-70 transition-opacity",
        variant === "success" && "bg-success/20",
        variant === "warning" && "bg-warning/20",
        variant === "destructive" && "bg-destructive/20",
        variant === "default" && "bg-primary/20"
      )} />
      
      <CardContent className="p-6 relative z-10">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs font-space uppercase tracking-widest text-muted-foreground mb-3">
              {title}
            </p>
            <p className={cn("text-3xl md:text-4xl font-oswald font-medium mb-2", variantStyles[variant])}>
              {value}
            </p>
            {subtitle && (
              <p className="text-sm text-muted-foreground mb-3">{subtitle}</p>
            )}
            {trend && (
              <div className="flex items-center gap-2 mt-3">
                {trend.isPositive ? (
                  <TrendingUp className={cn("w-4 h-4", "text-success")} />
                ) : (
                  <TrendingDown className={cn("w-4 h-4", "text-destructive")} />
                )}
                <span
                  className={cn(
                    "text-xs font-medium flex items-center gap-1",
                    trend.isPositive ? "text-success" : "text-destructive"
                  )}
                >
                  {Math.abs(trend.value)}%
                </span>
                <span className="text-xs text-muted-foreground">vs hier</span>
              </div>
            )}
          </div>
          <div className={cn(
            "w-14 h-14 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110",
            iconBgStyles[variant]
          )}>
            <Icon className={cn("w-7 h-7", variantStyles[variant])} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MetricCard;
