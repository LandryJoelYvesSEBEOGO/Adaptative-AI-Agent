import { NavLink as RouterNavLink, useLocation } from "react-router-dom";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarLinkProps {
  to: string;
  icon: LucideIcon;
  label: string;
  collapsed?: boolean;
}

const SidebarLink = ({ to, icon: Icon, label, collapsed }: SidebarLinkProps) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <RouterNavLink
      to={to}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group",
        isActive
          ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
          : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      )}
    >
      <Icon className={cn("w-5 h-5 shrink-0", isActive && "text-primary-foreground")} />
      {!collapsed && (
        <span className={cn(
          "text-sm font-medium transition-opacity",
          isActive ? "text-primary-foreground" : ""
        )}>
          {label}
        </span>
      )}
    </RouterNavLink>
  );
};

export default SidebarLink;
