# ⚠️ URL Importante à Retenir

## ❌ Ne PAS utiliser dans le navigateur :
```
http://0.0.0.0:8000
```
**Erreur** : `ERR_ADDRESS_INVALID`

## ✅ Utiliser à la place :

### Dans le navigateur :
```
http://localhost:8000
```
ou
```
http://127.0.0.1:8000
```

### URLs disponibles :

| Service | URL | Description |
|---------|-----|-------------|
| **API Racine** | http://localhost:8000 | Informations de l'API |
| **Health Check** | http://localhost:8000/health | Vérification du serveur |
| **Documentation Swagger** | http://localhost:8000/docs | Documentation interactive |
| **ReDoc** | http://localhost:8000/redoc | Documentation alternative |

## 🔍 Pourquoi ?

- `0.0.0.0` = **Adresse d'écoute du serveur** (toutes les interfaces réseau)
  - Utilisé par le serveur pour écouter sur toutes les interfaces
  - Ne peut pas être utilisé dans un navigateur

- `localhost` ou `127.0.0.1` = **Adresse d'accès depuis votre machine**
  - Utilisé dans le navigateur pour se connecter au serveur
  - Pointe vers votre propre machine

## 💡 Rappel

Quand vous voyez dans les logs :
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

Cela signifie que le serveur **écoute** sur toutes les interfaces, mais vous devez **accéder** via :
```
http://localhost:8000
```

