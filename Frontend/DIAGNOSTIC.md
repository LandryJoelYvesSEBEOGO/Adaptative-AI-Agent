# Diagnostic du Frontend

## Problème : Le frontend ne s'affiche pas

### Vérifications à faire :

1. **Vérifier que le serveur de développement démarre**
   ```bash
   cd Frontend
   npm run dev
   ```
   Le serveur devrait démarrer sur `http://localhost:8080`

2. **Vérifier la console du navigateur**
   - Ouvrir les outils de développement (F12)
   - Vérifier l'onglet Console pour les erreurs JavaScript
   - Vérifier l'onglet Network pour les erreurs de chargement

3. **Vérifier les erreurs de compilation**
   - Vérifier le terminal où `npm run dev` est lancé
   - Chercher les erreurs TypeScript ou de build

4. **Vérifier la configuration**
   - Port du serveur : 8080 (défini dans `vite.config.ts`)
   - URL de l'API : `http://127.0.0.1:8000/api/v1` (défini dans `src/services/config.ts`)

### Solutions possibles :

1. **Nettoyer le cache et réinstaller les dépendances**
   ```bash
   cd Frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run dev
   ```

2. **Vérifier les erreurs dans la console**
   - Ouvrir `http://localhost:8080` dans le navigateur
   - Ouvrir la console (F12)
   - Noter toutes les erreurs affichées

3. **Vérifier que le backend est démarré**
   - Le backend doit être accessible sur `http://127.0.0.1:8000`
   - Tester avec : `curl http://127.0.0.1:8000/health`

