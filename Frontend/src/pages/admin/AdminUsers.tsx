import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Search, Plus, MoreHorizontal, Users, UserPlus, UserMinus } from "lucide-react";
import MetricCard from "@/components/admin/MetricCard";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const mockUsers = [
  {
    id: "1",
    email: "jean.dupont@company.com",
    name: "Jean Dupont",
    role: "user",
    status: "active",
    createdAt: "2024-01-15",
    lastLogin: "2024-12-22 14:30",
    requestCount: 156,
  },
  {
    id: "2",
    email: "marie.martin@company.com",
    name: "Marie Martin",
    role: "admin",
    status: "active",
    createdAt: "2024-02-20",
    lastLogin: "2024-12-22 13:45",
    requestCount: 89,
  },
  {
    id: "3",
    email: "pierre.bernard@company.com",
    name: "Pierre Bernard",
    role: "user",
    status: "inactive",
    createdAt: "2024-03-10",
    lastLogin: "2024-11-15 09:20",
    requestCount: 45,
  },
  {
    id: "4",
    email: "sophie.petit@company.com",
    name: "Sophie Petit",
    role: "user",
    status: "active",
    createdAt: "2024-04-05",
    lastLogin: "2024-12-21 16:00",
    requestCount: 234,
  },
  {
    id: "5",
    email: "lucas.moreau@company.com",
    name: "Lucas Moreau",
    role: "user",
    status: "active",
    createdAt: "2024-05-12",
    lastLogin: "2024-12-22 10:15",
    requestCount: 78,
  },
];

const AdminUsers = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredUsers = mockUsers.filter(
    (user) =>
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-oswald font-medium tracking-tight">
            Gestion des Utilisateurs
          </h1>
          <p className="text-muted-foreground">
            Gérez les comptes utilisateurs et leurs permissions
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Nouvel utilisateur
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Utilisateurs Actifs"
          value="42"
          subtitle="30 derniers jours"
          icon={Users}
          variant="success"
        />
        <MetricCard
          title="Nouveaux ce mois"
          value="8"
          subtitle="Depuis le 1er déc."
          icon={UserPlus}
        />
        <MetricCard
          title="Inactifs"
          value="5"
          subtitle="> 30 jours"
          icon={UserMinus}
          variant="warning"
        />
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par nom ou email..."
              className="pl-10 max-w-md"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Liste des utilisateurs</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-4 text-xs font-space uppercase tracking-widest text-muted-foreground">
                    Utilisateur
                  </th>
                  <th className="text-left p-4 text-xs font-space uppercase tracking-widest text-muted-foreground">
                    Rôle
                  </th>
                  <th className="text-left p-4 text-xs font-space uppercase tracking-widest text-muted-foreground">
                    Statut
                  </th>
                  <th className="text-left p-4 text-xs font-space uppercase tracking-widest text-muted-foreground">
                    Dernière connexion
                  </th>
                  <th className="text-left p-4 text-xs font-space uppercase tracking-widest text-muted-foreground">
                    Requêtes
                  </th>
                  <th className="text-left p-4 text-xs font-space uppercase tracking-widest text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-border hover:bg-muted/30 transition-colors"
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-primary/10 text-primary text-sm">
                            {user.name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">{user.name}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <Badge
                        variant={user.role === "admin" ? "default" : "secondary"}
                      >
                        {user.role === "admin" ? "Admin" : "Utilisateur"}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <Badge
                        className={cn(
                          user.status === "active"
                            ? "bg-success hover:bg-success/90"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {user.status === "active" ? "Actif" : "Inactif"}
                      </Badge>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">
                      {user.lastLogin}
                    </td>
                    <td className="p-4 font-mono text-sm">{user.requestCount}</td>
                    <td className="p-4">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Modifier</DropdownMenuItem>
                          <DropdownMenuItem>Réinitialiser mot de passe</DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive">
                            Désactiver
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminUsers;
