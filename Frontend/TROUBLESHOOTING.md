# Guide de dépannage - Frontend ne s'affiche pas

## Étapes de diagnostic

### 1. Vérifier que le serveur démarre

```bash
cd Frontend
npm run dev
```

**Résultat attendu :**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: use --host to expose
```

### 2. Vérifier la console du navigateur

1. Ouvrir `http://localhost:8080` dans votre navigateur
2. Appuyer sur `F12` pour ouvrir les outils de développement
3. Vérifier l'onglet **Console** pour les erreurs JavaScript
4. Vérifier l'onglet **Network** pour les erreurs de chargement

### 3. Erreurs courantes et solutions

#### Erreur : "Cannot find module"
**Solution :** Réinstaller les dépendances
```bash
cd Frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### Erreur : "Port 8080 already in use"
**Solution :** Changer le port dans `vite.config.ts` ou arrêter le processus qui utilise le port

#### Erreur : "Failed to resolve import"
**Solution :** Vérifier que tous les fichiers importés existent et que les chemins sont corrects

#### Page blanche sans erreur
**Solution :** 
1. Vérifier que `index.html` contient `<div id="root"></div>`
2. Vérifier que `main.tsx` monte correctement l'application
3. Vérifier la console pour les erreurs React

### 4. Vérifier la configuration

- **Port du serveur** : 8080 (défini dans `vite.config.ts`)
- **URL de l'API** : `http://127.0.0.1:8000/api/v1` (défini dans `src/services/config.ts`)
- **Backend doit être démarré** : Vérifier que le backend est accessible

### 5. Test minimal

Si le problème persiste, tester avec un composant minimal :

1. Modifier temporairement `src/App.tsx` :
```tsx
const App = () => <div>Test - Frontend fonctionne !</div>;
export default App;
```

2. Si cela fonctionne, le problème vient d'un composant spécifique
3. Si cela ne fonctionne pas, le problème vient de la configuration Vite

### 6. Vérifier les logs du serveur

Dans le terminal où `npm run dev` est lancé, vérifier :
- Les erreurs de compilation TypeScript
- Les erreurs de build Vite
- Les warnings

### 7. Nettoyer le cache

```bash
cd Frontend
rm -rf node_modules .vite dist
npm install
npm run dev
```

