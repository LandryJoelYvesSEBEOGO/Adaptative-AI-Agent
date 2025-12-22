# Implémentation des Métriques Basiques

## ✅ Fichiers créés/modifiés

### Nouveaux fichiers

1. **`src/core/metrics.py`** - Système de collecte de métriques
   - Collecte les latences de chaque étape
   - Stocke dans `data/metrics/metrics.jsonl` (une ligne par requête)
   - Résumé dans `data/metrics/summary.json`
   - Calcul automatique des statistiques (moyenne, médiane, p95, p99)

2. **`src/core/logger.py`** - Logger structuré JSON
   - Logs JSON dans `data/logs/rag.log`
   - Format console lisible pour développement
   - Support des champs personnalisés (conversation_id, trace_id, data)

3. **`view_metrics.py`** - Script de visualisation
   - Affiche les métriques de manière lisible
   - Statistiques complètes des latences

### Fichiers modifiés

1. **`config/Config.py`**
   - Ajout de `project_root` (ligne 10)
   - Configuration métriques (METRICS_ENABLED, METRICS_DIR, LOGS_DIR)
   - Seuils d'alerte (ALERT_LATENCY_THRESHOLD, ALERT_ERROR_RATE_THRESHOLD)

2. **`src/rag/Rag_model.py`**
   - Ajout de `conversation_id` et `latencies` au `GraphState`
   - Intégration des métriques dans toutes les fonctions de nœuds :
     - `retrieve()` - mesure latence retrieval
     - `generate()` - mesure latence generation
     - `grade_documents()` - mesure latence grading
     - `web_search()` - mesure latence web_search
   - `get_final_response()` - mesure latence end-to-end et enregistre toutes les métriques
   - Logging structuré dans chaque fonction

3. **`src/core/__init__.py`**
   - Export de `get_metrics_collector` et `get_logger`

4. **`.gitignore`**
   - Ajout de `data/metrics/` et `data/logs/` pour ignorer les fichiers de métriques

## 📊 Métriques collectées

### Latences mesurées

- **end_to_end** : Temps total de la requête
- **retrieval** : Temps de récupération des documents
- **generation** : Temps de génération de la réponse
- **grading** : Temps de validation des documents
- **web_search** : Temps de recherche web (si utilisé)

### Autres métriques

- Nombre total de requêtes
- Nombre d'erreurs
- Taux d'erreur
- Nombre de documents récupérés
- Longueur de la réponse

## 🚀 Utilisation

### 1. Les métriques sont automatiquement collectées

Dès que vous utilisez `get_final_response()`, les métriques sont enregistrées automatiquement.

### 2. Visualiser les métriques

```bash
python view_metrics.py
```

Cela affichera :
- Nombre total de requêtes
- Taux d'erreur
- Statistiques détaillées pour chaque latence (moyenne, médiane, p95, p99, min, max)

### 3. Consulter les logs

Les logs structurés sont dans `data/logs/rag.log` (format JSON).

## 📁 Structure des fichiers

```
data/
├── metrics/
│   ├── metrics.jsonl      # Une ligne JSON par requête
│   └── summary.json       # Résumé agrégé
└── logs/
    └── rag.log            # Logs structurés JSON
```

## 🔍 Format des métriques

### Fichier metrics.jsonl (une ligne par requête)

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "conversation_id": "uuid-here",
  "query": "What is a Large Language Model?",
  "success": true,
  "error": null,
  "latencies": {
    "end_to_end": 4.5,
    "retrieval": 0.8,
    "generation": 2.1,
    "grading": 0.5,
    "web_search": 0.0
  },
  "num_documents": 3,
  "response_length": 450
}
```

### Fichier summary.json (résumé agrégé)

```json
{
  "total_requests": 100,
  "total_errors": 2,
  "latencies": {
    "end_to_end": [4.5, 3.2, 5.1, ...],
    "retrieval": [0.8, 0.6, 0.9, ...],
    ...
  },
  "last_updated": "2024-01-15T10:30:45.123456"
}
```

## ⚙️ Configuration

Dans `config/Config.py` :

```python
METRICS_ENABLED = True  # Activer/désactiver les métriques
ALERT_LATENCY_THRESHOLD = 10.0  # Alerter si latence > 10s
ALERT_ERROR_RATE_THRESHOLD = 0.05  # Alerter si taux d'erreur > 5%
```

## 🎯 Prochaines étapes

1. **Tester le système** : Faire quelques requêtes et visualiser les métriques
2. **Dashboard Grafana** (optionnel) : Créer un dashboard pour visualiser en temps réel
3. **Alerting** (optionnel) : Implémenter des alertes email/Slack si seuils dépassés
4. **Métriques avancées** : Ajouter métriques qualité (faithfulness, relevance, etc.)

## ✅ Checklist

- [x] Système de métriques créé
- [x] Logger structuré JSON créé
- [x] Intégration dans tous les nœuds
- [x] Script de visualisation créé
- [x] Configuration ajoutée
- [x] Fichiers ajoutés au .gitignore
- [ ] Tests effectués
- [ ] Dashboard Grafana (optionnel)

## 🐛 Dépannage

Si les métriques ne s'enregistrent pas :
1. Vérifier que `METRICS_ENABLED = True` dans `Config.py`
2. Vérifier que le dossier `data/metrics/` existe et est accessible en écriture
3. Vérifier les logs dans `data/logs/rag.log` pour voir les erreurs

