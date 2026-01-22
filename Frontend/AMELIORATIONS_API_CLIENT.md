# Améliorations du Client API

## 📋 Résumé des améliorations

Le client API a été complètement refactorisé pour offrir une meilleure gestion des erreurs, des timeouts, et une préparation pour le refresh token.

## 🆕 Nouveaux fichiers créés

### 1. `src/services/config.ts`
- Configuration centralisée de l'API
- URL de base, timeout, clés de stockage

### 2. `src/services/apiError.ts`
- Classe `ApiError` personnalisée
- Méthodes utilitaires pour identifier le type d'erreur
- Messages utilisateur-friendly

### 3. `src/services/apiClient.ts`
- Fonction `apiRequest` améliorée avec :
  - Gestion du timeout (AbortController)
  - Gestion automatique des tokens
  - Préparation pour refresh token
  - Support de différents types de contenu (JSON, blob, texte)
  - Gestion d'erreurs améliorée

## 🔄 Fichiers modifiés

### `src/services/api.ts`
- Refactorisé pour utiliser le nouveau `apiClient`
- Timeouts configurables par méthode
- Meilleure gestion d'erreurs avec `ApiError`
- Streaming amélioré avec gestion de buffer

### `src/stores/authStore.ts`
- Gestion des `ApiError` avec messages utilisateur-friendly
- Meilleure gestion des erreurs de connexion/inscription

### `src/App.tsx`
- Ajout d'un listener pour l'événement `auth:expired`
- Déconnexion automatique en cas d'expiration de session

### `src/pages/Chat.tsx`
- Gestion améliorée des erreurs avec `ApiError`
- Messages d'erreur plus clairs pour l'utilisateur

## ✨ Fonctionnalités ajoutées

### 1. Gestion du Timeout
- Timeout configurable par requête
- Timeout par défaut : 30 secondes
- Timeout spécifique pour certaines opérations :
  - Login/Register : 10 secondes
  - Chat RAG : 60 secondes
  - Streaming : 120 secondes (2 minutes)
  - Admin : 10 secondes

### 2. Gestion d'erreurs améliorée
- Classe `ApiError` avec :
  - `isTimeout()` - Vérifie si c'est un timeout
  - `isUnauthorized()` - Vérifie si c'est une erreur 401
  - `isForbidden()` - Vérifie si c'est une erreur 403
  - `isNotFound()` - Vérifie si c'est une erreur 404
  - `isServerError()` - Vérifie si c'est une erreur serveur (5xx)
  - `getUserMessage()` - Message utilisateur-friendly

### 3. Préparation pour Refresh Token
- Structure prête pour le refresh token
- Méthode `refreshAccessToken()` préparée (non active car backend ne le supporte pas encore)
- Gestion automatique de la ré-authentification en cas de 401

### 4. Support de différents types de contenu
- JSON (par défaut)
- Blob (PDF, images, etc.)
- Texte brut
- Streaming SSE

### 5. Gestion automatique de l'expiration de session
- Événement `auth:expired` déclenché automatiquement
- Déconnexion et redirection automatiques
- Listener dans `App.tsx` pour gérer globalement

## 🔧 Utilisation

### Exemple avec timeout personnalisé
```typescript
const response = await apiClient.queryRAG(
  "Qu'est-ce que le RAG?",
  undefined,
  { timeout: 90000 } // 90 secondes
);
```

### Exemple avec gestion d'erreurs
```typescript
try {
  const response = await apiClient.getMetricsOverview();
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isTimeout()) {
      // Gérer le timeout
    } else if (error.isUnauthorized()) {
      // Gérer l'expiration de session
    } else {
      // Afficher le message utilisateur-friendly
      toast.error(error.getUserMessage());
    }
  }
}
```

### Exemple avec streaming et gestion d'erreurs
```typescript
await apiClient.queryRAGStream(
  question,
  conversationId,
  (chunk) => {
    // Traiter le chunk
  },
  {
    timeout: 180000, // 3 minutes
    onError: (error) => {
      console.error('Erreur de streaming:', error);
    }
  }
);
```

## 📝 Notes importantes

1. **Refresh Token** : Le code est préparé mais non actif car le backend ne supporte pas encore `/auth/refresh`. Il sera activé automatiquement quand le backend l'implémentera.

2. **Compatibilité** : Toutes les fonctionnalités existantes continuent de fonctionner. Les améliorations sont rétrocompatibles.

3. **Timeouts** : Les timeouts sont maintenant configurables et plus appropriés selon le type d'opération.

4. **Messages d'erreur** : Les messages sont maintenant plus clairs et utilisateur-friendly grâce à `getUserMessage()`.

## 🚀 Prochaines étapes possibles

1. Implémenter le refresh token côté backend
2. Ajouter un système de retry automatique pour les erreurs réseau
3. Ajouter un cache pour certaines requêtes (métriques, etc.)
4. Ajouter des métriques de performance côté client

