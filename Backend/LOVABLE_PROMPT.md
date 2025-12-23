# Prompt pour Lovable - Interface RAG avec Dashboard Admin

## Vue d'ensemble du projet

Je souhaite créer une application web moderne pour un système RAG (Retrieval-Augmented Generation) avec deux interfaces distinctes selon le type d'utilisateur :

1. **Interface Administrateur** : Dashboard complet avec métriques, analytics et gestion du système
2. **Interface Utilisateur/Employé** : Interface de chat simple et intuitive pour interagir avec le RAG

---

## Système d'authentification et de rôles

### Deux types de connexion/inscription :

#### 1. **Inscription/Connexion Administrateur**
- **Route** : `/admin/login` ou `/admin/register`
- **Fonctionnalités** :
  - Formulaire d'inscription avec validation email
  - Connexion sécurisée avec JWT tokens
  - Gestion des sessions admin
  - Protection des routes admin (middleware d'authentification)
  - Mot de passe oublié / réinitialisation
  - Option "Se souvenir de moi"

#### 2. **Connexion Utilisateur/Employé**
- **Route** : `/user/login` ou `/login`
- **Fonctionnalités** :
  - Connexion simplifiée (email + mot de passe)
  - Pas d'inscription publique (gestion par admin)
  - Session utilisateur standard
  - Accès direct au chat après connexion
  - Option "Se souvenir de moi"

### Gestion des rôles :
- **Système de rôles** : `admin` | `user`
- **Middleware de protection** : Vérification du rôle avant accès aux routes
- **Redirection automatique** : Après connexion, redirection selon le rôle
- **Déconnexion** : Bouton déconnexion avec confirmation

---

## INTERFACE ADMINISTRATEUR - Dashboard

### Page principale : `/admin/dashboard`

#### **Layout général** :
- **Sidebar gauche** : Navigation avec icônes
  - Dashboard (accueil)
  - Métriques & Performance
  - Requêtes API
  - Qualité des réponses
  - Utilisateurs (gestion)
  - Paramètres système
  - Déconnexion
- **Header** : 
  - Logo / Nom de l'application
  - Badge "Administrateur"
  - Notifications (si applicable)
  - Profil admin (menu déroulant)
- **Zone principale** : Contenu du dashboard avec widgets

---

### **1. Vue d'ensemble (Overview) - Page d'accueil du dashboard**

#### Widgets principaux (Cards) :

**A. Statistiques globales (4 cards en ligne)** :
- **Total Requêtes** : Nombre total de requêtes depuis le début
  - Couleur : Bleu
  - Sous-texte : "Toutes les requêtes"
  - Graphique sparkline (tendance 7 derniers jours)

- **Requêtes aujourd'hui** : Nombre de requêtes du jour
  - Couleur : Vert
  - Comparaison avec hier (+X% ou -X%)
  - Graphique sparkline (tendance 24h)

- **Taux de succès** : Pourcentage de requêtes réussies
  - Couleur : Vert (si > 95%), Orange (si 90-95%), Rouge (< 90%)
  - Affichage : "X% (Y échecs)"
  - Indicateur visuel (barre de progression)

- **Temps de réponse moyen** : Latence moyenne end-to-end
  - Couleur : Bleu
  - Affichage : "X.Xs"
  - Comparaison avec objectif (< 5s)

**B. Graphique de tendance (Line Chart)** :
- **Requêtes par jour** (7 derniers jours ou 30 jours)
  - Axe X : Dates
  - Axe Y : Nombre de requêtes
  - Ligne : Requêtes totales
  - Ligne secondaire : Requêtes réussies (vert) vs échecs (rouge)
  - Tooltip : Détails au survol
  - Sélecteur de période : 7j / 30j / 90j / Tout

**C. Répartition des erreurs (Pie Chart ou Donut Chart)** :
- Types d'erreurs :
  - Timeout
  - Erreur LLM
  - Erreur retrieval
  - Erreur web search
  - Autres
- Pourcentage et nombre pour chaque type
- Couleurs distinctes

**D. Activité récente (Table)** :
- Liste des 10 dernières requêtes
- Colonnes :
  - Timestamp (format relatif : "Il y a 2 min")
  - Utilisateur (email ou ID)
  - Question (tronquée à 50 caractères)
  - Statut (Succès / Échec)
  - Latence (X.Xs)
  - Action : Bouton "Voir détails"

---

### **2. Page Métriques & Performance** : `/admin/metrics`

#### **A. Latences détaillées** :

**Section : Statistiques de latence**
- **Tableau de métriques** avec colonnes :
  - Métrique | Count | Moyenne | Médiane | P95 | P99 | Min | Max
  - Métriques à afficher :
    - **End-to-End** : Temps total de la requête
    - **Retrieval** : Temps de récupération des documents
    - **Generation** : Temps de génération de la réponse
    - **Grading** : Temps d'évaluation (documents, hallucination, réponse)
    - **Web Search** : Temps de recherche web
    - **Answer Quality** : Temps d'évaluation de la qualité

**Graphiques de latence** :
- **Line Chart** : Évolution des latences dans le temps
  - Une ligne par métrique
  - Sélecteur de période
  - Légende interactive (clic pour afficher/masquer)
- **Box Plot** : Distribution des latences
  - Un box plot par métrique
  - Affichage des quartiles, médiane, outliers

**Alertes de performance** :
- Cards d'alerte si :
  - Latence moyenne > 10s (seuil configurable)
  - Taux d'erreur > 5% (seuil configurable)
  - P95 > 15s
- Couleur : Rouge
- Message : "Attention : [description du problème]"

#### **B. Métriques de Retrieval** :

**Section : Performance du retrieval**
- **Precision@K** : Pour différentes valeurs de K (1, 3, 5, 10)
  - Graphique bar chart
  - Affichage : "Precision@1: X%, Precision@3: Y%, ..."
- **Recall@K** : Pour différentes valeurs de K
  - Graphique bar chart
- **MAP (Mean Average Precision)** : Score global
  - Card avec valeur principale
  - Graphique de tendance (évolution dans le temps)

**Tableau des dernières recherches** :
- Colonnes :
  - Timestamp
  - Query (question)
  - Nombre de documents récupérés
  - Precision@K
  - Recall@K
  - Sources (liste des sources récupérées)

---

### **3. Page Requêtes API** : `/admin/api-requests`

#### **A. Statistiques API** :

**Cards principales** :
- **Total Requêtes API** : Nombre total depuis le début
- **Requêtes aujourd'hui** : Avec comparaison
- **Coût estimé** : Si applicable (calcul basé sur tokens)
- **Taux d'utilisation** : Requêtes/heure moyenne

**Graphique d'utilisation** :
- **Area Chart** : Requêtes par heure (24h) ou par jour
  - Zone colorée avec dégradé
  - Tooltip avec détails

#### **B. Liste des requêtes** :

**Tableau avec filtres et recherche** :
- **Filtres** :
  - Par date (sélecteur de période)
  - Par statut (Succès / Échec / Tous)
  - Par utilisateur (dropdown)
  - Par type de requête (si applicable)
- **Recherche** : Barre de recherche (par question, ID, utilisateur)
- **Tri** : Par date (récent/premier), par latence, par statut

**Colonnes du tableau** :
- Checkbox (sélection multiple)
- ID Requête (lien cliquable)
- Timestamp (format : "2024-01-15 14:30:25")
- Utilisateur
- Question (tronquée, tooltip avec texte complet)
- Statut (badge coloré)
- Latence (end-to-end)
- Documents récupérés (nombre)
- Qualité réponse (score 0-1, si disponible)
- Actions :
  - Voir détails (modal)
  - Copier ID
  - Supprimer (avec confirmation)

**Pagination** :
- 25 / 50 / 100 résultats par page
- Navigation : Première, Précédente, Suivante, Dernière
- Affichage : "Affichage de X à Y sur Z résultats"

#### **C. Modal de détails d'une requête** :

**Contenu du modal** :
- **Informations générales** :
  - ID Requête
  - Timestamp complet
  - Utilisateur
  - Statut
- **Question complète** : Texte intégral
- **Réponse générée** : Texte complet avec formatage
- **Documents récupérés** :
  - Liste avec preview (premiers 200 caractères)
  - Sources (liens si disponibles)
  - Scores de similarité (si disponibles)
- **Métriques détaillées** :
  - Latences par étape (retrieval, generation, etc.)
  - Scores de qualité (relevance, completeness, etc.)
  - Nombre de tokens (si disponible)
- **Erreurs** : Si échec, afficher le message d'erreur complet
- **Actions** :
  - Fermer
  - Exporter en JSON
  - Copier toutes les infos

---

### **4. Page Qualité des Réponses** : `/admin/answer-quality`

#### **A. Scores globaux** :

**Cards de scores moyens** :
- **Score global moyen** : Score de qualité moyen (0-1)
  - Affichage : "X.XX / 1.00"
  - Graphique : Gauge chart (jauge circulaire)
  - Couleur : Vert (> 0.8), Orange (0.6-0.8), Rouge (< 0.6)

**Scores par critère** (5 cards) :
- **Relevance** (Pertinence) : Score moyen
  - Barre de progression
  - Graphique de tendance
- **Completeness** (Complétude) : Score moyen
  - Barre de progression
  - Graphique de tendance
- **Conciseness** (Concision) : Score moyen
  - Barre de progression
  - Graphique de tendance
- **Accuracy** (Précision) : Score moyen
  - Barre de progression
  - Graphique de tendance
- **Coherence** (Cohérence) : Score moyen
  - Barre de progression
  - Graphique de tendance

#### **B. Distribution des scores** :

**Graphiques** :
- **Histogramme** : Distribution du score global
  - Bins de 0.1 (0-0.1, 0.1-0.2, ..., 0.9-1.0)
  - Nombre de réponses par bin
  - Couleur : Dégradé (rouge → vert)

- **Box Plot par critère** : Distribution de chaque critère
  - 5 box plots côte à côte
  - Affichage des quartiles, médiane, outliers

#### **C. Évolution de la qualité** :

**Line Chart** : Score moyen dans le temps
- Ligne principale : Score global moyen
- Lignes secondaires : Scores par critère (optionnel, toggle)
- Période : 7j / 30j / 90j
- Tooltip : Valeurs détaillées au survol

#### **D. Réponses à faible qualité** :

**Tableau des réponses avec score < seuil** :
- Filtre : Score < 0.6 (configurable)
- Colonnes :
  - Timestamp
  - Question
  - Réponse (tronquée)
  - Score global
  - Scores par critère (mini barres)
  - Action : Voir détails

---

### **5. Page Gestion Utilisateurs** : `/admin/users`

#### **A. Liste des utilisateurs** :

**Tableau avec recherche et filtres** :
- **Recherche** : Par email, nom, ID
- **Filtres** :
  - Par rôle (Admin / User)
  - Par statut (Actif / Inactif)
  - Par date d'inscription

**Colonnes** :
- Avatar (initiale ou icône par défaut)
- Email
- Nom (si disponible)
- Rôle (badge)
- Statut (Actif / Inactif)
- Date inscription
- Dernière connexion
- Nombre de requêtes
- Actions :
  - Modifier
  - Réinitialiser mot de passe
  - Désactiver/Activer
  - Supprimer (avec confirmation)

#### **B. Statistiques par utilisateur** :

**Card de statistiques** :
- Utilisateurs actifs (30 derniers jours)
- Nouveaux utilisateurs (ce mois)
- Utilisateurs inactifs (> 30 jours)

**Graphique** :
- **Bar Chart** : Top 10 utilisateurs par nombre de requêtes
  - Nom/Email
  - Nombre de requêtes
  - Score moyen de qualité

#### **C. Création/Modification d'utilisateur** :

**Modal de création/édition** :
- Formulaire :
  - Email (required, validation)
  - Nom (optionnel)
  - Rôle (dropdown : Admin / User)
  - Mot de passe (required pour création, optionnel pour édition)
  - Statut (Actif / Inactif)
- Actions :
  - Enregistrer
  - Annuler

---

### **6. Page Paramètres Système** : `/admin/settings`

#### **A. Configuration RAG** :

**Sections configurables** :
- **Modèles** :
  - Modèle LLM principal (dropdown)
  - Modèle de fallback (dropdown)
  - Modèle d'embedding (affichage)
- **Retrieval** :
  - Nombre de documents à récupérer (slider : 1-20)
  - Seuil de similarité (slider : 0-1)
  - Hybrid search (toggle on/off)
- **Génération** :
  - Température (slider : 0-2)
  - Max tokens (input number)
  - Streaming (toggle on/off)

#### **B. Seuils d'alerte** :

**Configuration des alertes** :
- Latence seuil (secondes) : Input number
- Taux d'erreur seuil (%) : Input number
- Email notifications (toggle)
- Webhook pour alertes (input URL)

#### **C. Export de données** :

**Options d'export** :
- Exporter toutes les métriques (CSV/JSON)
- Exporter les requêtes (CSV/JSON)
- Exporter les métriques de qualité (CSV/JSON)
- Période : Sélecteur de dates
- Bouton "Exporter"

#### **D. Sauvegarde** :
- Bouton "Enregistrer les paramètres"
- Message de confirmation après sauvegarde
- Validation des valeurs avant sauvegarde

---

## INTERFACE UTILISATEUR - Chat

### Page principale : `/chat` ou `/`

#### **Layout** :

**Header simple** :
- Logo / Nom de l'application
- Badge "Utilisateur" ou nom de l'utilisateur
- Menu (icône hamburger) :
  - Mon profil
  - Historique des conversations
  - Paramètres
  - Déconnexion

**Zone de chat (centrée, largeur max 900px)** :
- **Zone des messages** :
  - Scroll automatique vers le bas
  - Messages utilisateur (alignés à droite, bulle bleue)
  - Messages assistant (alignés à gauche, bulle grise/blanche)
  - Timestamp discret sous chaque message
  - Citations cliquables : [1], [2], [3] avec tooltip montrant la source
  - Animation de frappe (typing indicator) pendant la génération

**Zone de saisie** :
- **Input text** :
  - Placeholder : "Posez votre question..."
  - Multiline (textarea avec auto-resize)
  - Bouton d'envoi (icône envoi ou "Entrée")
  - Indicateur de caractères (optionnel)
- **Boutons d'action** :
  - Effacer la conversation
  - Copier la dernière réponse
  - Paramètres (modal)

**Sidebar (optionnelle, collapsible)** :
- Historique des conversations récentes
- Recherche dans l'historique
- Nouvelle conversation (bouton)

---

### **Fonctionnalités du chat** :

#### **1. Streaming des réponses** :
- Affichage token par token (streaming)
- Animation fluide de frappe
- Indicateur "L'assistant écrit..." pendant la génération
- Fallback automatique si streaming échoue

#### **2. Citations automatiques** :
- Format : [1], [2], [3] dans le texte
- **Citations cliquables** :
  - Au clic : Modal ou tooltip avec :
    - Source du document
    - Extrait du document (premiers 300 caractères)
    - Lien vers le document complet (si disponible)
- Style visuel : Liens bleus soulignés
- Hover effect : Changement de couleur

#### **3. Historique des conversations** :
- **Page** : `/chat/history`
- Liste des conversations :
  - Titre (première question ou "Nouvelle conversation")
  - Date et heure
  - Nombre de messages
  - Preview (dernière question)
- Actions :
  - Ouvrir la conversation
  - Supprimer (avec confirmation)
  - Exporter (JSON/Markdown)
- Recherche : Barre de recherche pour filtrer

#### **4. Feedback utilisateur** :
- **Boutons sous chaque réponse** :
  - Utile (like)
  - Pas utile (dislike)
  - Signaler un problème
- **Modal de feedback** (si pas utile ou signaler) :
  - Raison (dropdown) :
    - Réponse incorrecte
    - Réponse incomplète
    - Réponse non pertinente
    - Autre
  - Commentaire (textarea optionnel)
  - Envoyer
- Enregistrement du feedback dans les métriques

#### **5. Suggestions de questions follow-up** :
- **Section sous la réponse** :
  - Titre : "Questions suggérées :"
  - 3-4 boutons avec questions suggérées
  - Exemples :
    - "Peux-tu donner plus de détails sur [sujet] ?"
    - "Quels sont les avantages de [concept] ?"
    - "Comment fonctionne [processus] ?"
- Clic sur suggestion : Insère la question dans l'input et envoie automatiquement

#### **6. Paramètres utilisateur** :
- **Modal de paramètres** :
  - Thème (Clair / Sombre / Auto)
  - Taille de police (Petite / Normale / Grande)
  - Langue (si multilingue)
  - Notifications (toggle)
  - Effacer toutes les conversations (avec confirmation)

---

## Design et UX

### **Style général** :
- **Framework CSS** : Tailwind CSS ou Material-UI
- **Thème** :
  - Mode clair par défaut
  - Mode sombre (toggle dans header)
  - Palette de couleurs :
    - Primaire : Bleu (#3B82F6 ou similaire)
    - Succès : Vert (#10B981)
    - Erreur : Rouge (#EF4444)
    - Avertissement : Orange (#F59E0B)
    - Neutre : Gris (#6B7280)

### **Composants réutilisables** :
- **Cards** : Ombres subtiles, bordures arrondies
- **Tables** : Lignes alternées, hover effect, responsive
- **Graphiques** : Utiliser Chart.js, Recharts, ou D3.js
- **Modals** : Overlay sombre, animation d'ouverture/fermeture
- **Boutons** : États hover, active, disabled
- **Inputs** : Validation visuelle (vert si valide, rouge si erreur)
- **Loading states** : Spinners, skeletons, progress bars

### **Responsive Design** :
- **Desktop** : Layout complet avec sidebar
- **Tablet** : Sidebar collapsible, adaptation des graphiques
- **Mobile** : 
  - Sidebar en drawer (slide-in)
  - Tableaux scrollables horizontalement
  - Graphiques adaptés (légendes empilées)
  - Chat en plein écran

### **Animations** :
- Transitions fluides (200-300ms)
- Hover effects sur les éléments interactifs
- Loading animations (spinners, skeletons)
- Notifications toast (slide-in depuis le haut)

### **Accessibilité** :
- Contraste de couleurs (WCAG AA minimum)
- Navigation au clavier (Tab, Enter, Esc)
- Labels ARIA pour les lecteurs d'écran
- Focus visible sur les éléments interactifs

---

## Technologies recommandées

### **Frontend** :
- **Framework** : React avec TypeScript
- **Routing** : React Router
- **State Management** : Zustand ou Redux Toolkit
- **UI Components** : 
  - Shadcn/ui ou
  - Material-UI (MUI) ou
  - Ant Design
- **Graphiques** : Recharts ou Chart.js
- **Forms** : React Hook Form + Zod (validation)
- **HTTP Client** : Axios ou Fetch API
- **Authentication** : JWT avec localStorage/sessionStorage

### **Backend API** (à intégrer) :
- **Endpoints nécessaires** :
  - `POST /api/auth/login` (admin/user)
  - `POST /api/auth/register` (admin uniquement)
  - `GET /api/metrics/summary`
  - `GET /api/metrics/statistics`
  - `GET /api/requests` (avec pagination, filtres)
  - `GET /api/requests/:id`
  - `GET /api/answer-quality/stats`
  - `GET /api/users`
  - `POST /api/chat` (streaming)
  - `GET /api/chat/history`
  - `POST /api/feedback`

---

## Pages et Routes

### **Routes publiques** :
- `/` : Page d'accueil (redirection vers login si non connecté)
- `/login` : Connexion utilisateur
- `/admin/login` : Connexion administrateur

### **Routes utilisateur** (protégées, rôle: user) :
- `/chat` : Interface de chat principale
- `/chat/history` : Historique des conversations
- `/profile` : Profil utilisateur

### **Routes admin** (protégées, rôle: admin) :
- `/admin/dashboard` : Dashboard principal
- `/admin/metrics` : Métriques détaillées
- `/admin/api-requests` : Gestion des requêtes
- `/admin/answer-quality` : Qualité des réponses
- `/admin/users` : Gestion des utilisateurs
- `/admin/settings` : Paramètres système

---

## Checklist de fonctionnalités

### **Authentification** :
- [ ] Inscription admin
- [ ] Connexion admin
- [ ] Connexion utilisateur
- [ ] Gestion des sessions (JWT)
- [ ] Protection des routes par rôle
- [ ] Déconnexion
- [ ] Mot de passe oublié (optionnel)

### **Dashboard Admin** :
- [ ] Vue d'ensemble avec widgets
- [ ] Graphiques de tendance
- [ ] Métriques de latence
- [ ] Métriques de retrieval (Precision, Recall, MAP)
- [ ] Liste des requêtes avec filtres
- [ ] Détails d'une requête (modal)
- [ ] Scores de qualité des réponses
- [ ] Gestion des utilisateurs
- [ ] Paramètres système
- [ ] Export de données

### **Interface Chat** :
- [ ] Chat avec streaming
- [ ] Citations cliquables
- [ ] Historique des conversations
- [ ] Feedback utilisateur
- [ ] Suggestions de questions
- [ ] Paramètres utilisateur
- [ ] Mode sombre/clair

### **Design** :
- [ ] Responsive (mobile, tablet, desktop)
- [ ] Animations fluides
- [ ] Accessibilité (WCAG)
- [ ] Thème clair/sombre

---

## Points d'attention

1. **Performance** :
   - Lazy loading des composants lourds (graphiques)
   - Pagination pour les grandes listes
   - Debounce sur les recherches
   - Cache des données de métriques (si possible)

2. **Sécurité** :
   - Validation côté client ET serveur
   - Protection CSRF
   - Sanitization des inputs
   - Rate limiting sur les API

3. **Expérience utilisateur** :
   - Messages d'erreur clairs
   - Confirmations pour actions destructives
   - Loading states partout
   - Feedback visuel immédiat

4. **Intégration backend** :
   - Les endpoints API doivent être documentés
   - Gestion des erreurs API (retry, fallback)
   - Format de réponse standardisé (JSON)

---

## Notes supplémentaires

- **Backend existant** : Le backend RAG est en Python (Streamlit actuellement). Il faudra créer une API REST (FastAPI ou Flask) pour exposer les données au frontend React.
- **Base de données** : Pour l'authentification et le stockage des métriques, une base de données (PostgreSQL, MongoDB, ou SQLite) sera nécessaire.
- **Real-time** : Pour les métriques en temps réel, considérer WebSockets ou Server-Sent Events (SSE).

---

**Ce prompt est complet et détaillé. Utilisez-le avec Lovable pour générer l'interface complète. N'hésitez pas à itérer et affiner selon vos besoins spécifiques.**

