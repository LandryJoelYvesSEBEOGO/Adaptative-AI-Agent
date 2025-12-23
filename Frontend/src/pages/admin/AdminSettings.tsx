import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Save, Download, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const AdminSettings = () => {
  const { toast } = useToast();

  const handleSave = () => {
    toast({
      title: "Paramètres sauvegardés",
      description: "Vos modifications ont été enregistrées avec succès.",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-oswald font-medium tracking-tight">
          Paramètres Système
        </h1>
        <p className="text-muted-foreground">
          Configuration du système RAG et des alertes
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RAG Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Configuration RAG</CardTitle>
            <CardDescription>
              Paramètres des modèles et du retrieval
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Modèle LLM Principal</Label>
              <Select defaultValue="gpt-4">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4">GPT-4 Turbo</SelectItem>
                  <SelectItem value="gpt-3.5">GPT-3.5 Turbo</SelectItem>
                  <SelectItem value="claude">Claude 3 Opus</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Modèle de Fallback</Label>
              <Select defaultValue="gpt-3.5">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-3.5">GPT-3.5 Turbo</SelectItem>
                  <SelectItem value="claude-haiku">Claude 3 Haiku</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Documents à récupérer</Label>
                <span className="text-sm font-mono text-muted-foreground">5</span>
              </div>
              <Slider defaultValue={[5]} min={1} max={20} step={1} />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Seuil de similarité</Label>
                <span className="text-sm font-mono text-muted-foreground">0.7</span>
              </div>
              <Slider defaultValue={[70]} min={0} max={100} step={5} />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Hybrid Search</Label>
                <p className="text-xs text-muted-foreground">
                  Combiner recherche sémantique et BM25
                </p>
              </div>
              <Switch defaultChecked />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Streaming</Label>
                <p className="text-xs text-muted-foreground">
                  Afficher les réponses en temps réel
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>

        {/* Alert Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Seuils d'Alerte</CardTitle>
            <CardDescription>
              Configuration des notifications de performance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Seuil de latence (secondes)</Label>
              <Input type="number" defaultValue="10" />
            </div>

            <div className="space-y-2">
              <Label>Seuil taux d'erreur (%)</Label>
              <Input type="number" defaultValue="5" />
            </div>

            <div className="space-y-2">
              <Label>Email de notification</Label>
              <Input type="email" placeholder="admin@company.com" />
            </div>

            <div className="space-y-2">
              <Label>Webhook URL (optionnel)</Label>
              <Input type="url" placeholder="https://..." />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Notifications Email</Label>
                <p className="text-xs text-muted-foreground">
                  Recevoir des alertes par email
                </p>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>

        {/* Export */}
        <Card>
          <CardHeader>
            <CardTitle>Export de Données</CardTitle>
            <CardDescription>
              Télécharger les données du système
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button variant="outline" className="w-full justify-start">
              <Download className="w-4 h-4 mr-2" />
              Exporter les métriques (CSV)
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Download className="w-4 h-4 mr-2" />
              Exporter les requêtes (JSON)
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Download className="w-4 h-4 mr-2" />
              Exporter les scores qualité (CSV)
            </Button>
          </CardContent>
        </Card>

        {/* System */}
        <Card>
          <CardHeader>
            <CardTitle>Maintenance</CardTitle>
            <CardDescription>
              Actions de maintenance du système
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button variant="outline" className="w-full justify-start">
              <RefreshCw className="w-4 h-4 mr-2" />
              Réindexer la base vectorielle
            </Button>
            <Button variant="outline" className="w-full justify-start text-destructive hover:text-destructive">
              Vider le cache
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} size="lg">
          <Save className="w-4 h-4 mr-2" />
          Enregistrer les paramètres
        </Button>
      </div>
    </div>
  );
};

export default AdminSettings;
