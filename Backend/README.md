# 🤖 Agent RAG Adaptatif avec LangGraph

Un agent intelligent de question-réponse utilisant la génération augmentée par récupération (RAG) avec LangGraph. Cet agent combine la recherche dans une base de connaissances locale (vecteurs) et la recherche web pour fournir des réponses précises et contextuelles.

## 📋 Description

Cet agent RAG est construit avec :
- **LangGraph** : Orchestration du workflow adaptatif
- **Groq API** : Modèle de langage (LLaMA 3)
- **ChromaDB** : Base de données vectorielle pour le stockage et la récupération de documents
- **Nomic Embeddings** : Modèle d'embedding pour la représentation vectorielle
- **Tavily** : Recherche web pour les questions nécessitant des informations à jour
- **Streamlit** : Interface utilisateur web interactive
- **Whisper** : Transcription audio en texte

## ✨ Fonctionnalités

- 🔍 **Recherche adaptative** : Décide automatiquement entre recherche vectorielle et recherche web
- 📚 **Base de connaissances** : Supporte les documents PDF et les pages web
- 🌐 **Recherche web** : Accès à des informations récentes via Tavily
- 🎤 **Enregistrement vocal** : Possibilité de poser des questions par voix
- 🧠 **Évaluation de pertinence** : Vérifie la qualité et la pertinence des réponses générées
- 🔄 **Retry automatique** : Réessaie automatiquement en cas de réponse insuffisante

## 📦 Prérequis

- Python 3.8 ou supérieur
- CUDA (optionnel, pour accélérer les embeddings et la transcription)
- Microphone (pour la fonctionnalité vocale)

## 🚀 Installation

### 1. Cloner le repository

```bash
git clone <url-du-repository>
cd "RAG Model using Rerank model - Copie"
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

**Windows (PowerShell) :**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD) :**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac :**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances

**Méthode recommandée :** Utilisez le fichier `requirement.txt` pour installer toutes les dépendances :

```bash
cd Backend
pip install -r requirement.txt
```

**Note importante :** Dans LangChain 0.3.0+, `text_splitter` a été déplacé vers le package `langchain-text-splitters` qui est inclus dans `requirement.txt`. Utilisez `from langchain_text_splitters import RecursiveCharacterTextSplitter` dans votre code.

**Note pour PyAudio :** Sur Windows, si l'installation échoue, utilisez :
```bash
pip install pipwin
pipwin install pyaudio
```

## 🔑 Configuration

### 1. Créer un fichier `.env`

Créez un fichier `.env` à la racine du projet avec les clés API suivantes :

```env
GROQ_API_KEY=votre_clé_groq
TAVILY_API_KEY=votre_clé_tavily
LANGSMITH_API_KEY=votre_clé_langsmith
```

### 2. Obtenir les clés API

- **Groq API** : Obtenez votre clé sur [console.groq.com](https://console.groq.com)
- **Tavily API** : Obtenez votre clé sur [tavily.com](https://tavily.com)
- **LangSmith API** (optionnel) : Pour le suivi et le débogage, obtenez votre clé sur [smith.langchain.com](https://smith.langchain.com)

### 3. Préparer les documents

Placez vos fichiers PDF dans le dossier `data/raw/` si vous souhaitez les inclure dans la base de connaissances.

## ▶️ Lancement de l'application

### Lancer l'interface Streamlit

Depuis la racine du projet, exécutez :

```bash
streamlit run src/main.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`.

### Première exécution

Lors de la première exécution, le système va :
1. Télécharger les documents depuis les URLs configurées
2. Charger les PDFs du dossier `data/raw/`
3. Créer la base de données vectorielle ChromaDB dans `data/chroma_db/`

Cette étape peut prendre quelques minutes selon le nombre et la taille des documents.

## 📖 Utilisation

### Interface de chat

1. **Posez une question** : Tapez votre question dans le champ de saisie
2. **Réponse adaptative** : L'agent décidera automatiquement s'il doit :
   - Rechercher dans la base de connaissances locale
   - Effectuer une recherche web
   - Combiner les deux sources

### Enregistrement vocal

1. Cliquez sur **"🎤 Démarrer l'enregistrement"** dans la barre latérale
2. Parlez votre question
3. Cliquez sur **"⏹️ Arrêter l'enregistrement"**
4. Cliquez sur **"Transcrire l'audio"**
5. La transcription sera automatiquement insérée comme question

## 🏗️ Structure du projet

```
.
├── config/
│   └── Config.py              # Configuration et variables d'environnement
├── data/
│   ├── chroma_db/             # Base de données vectorielle (générée automatiquement)
│   └── raw/                   # Dossier pour vos fichiers PDF
├── src/
│   ├── main.py                # Point d'entrée Streamlit
│   ├── audio/
│   │   └── Speech_To_Text.py  # Gestion de l'enregistrement et transcription audio
│   └── rag/
│       ├── Rag_model.py       # Modèle RAG et workflow LangGraph
│       ├── Data_processing.py # Traitement et chargement des documents
│       └── Prompts.py         # Prompts utilisés par le système
└── README.md
```

## 🔧 Configuration avancée

### Modifier les modèles

Vous pouvez modifier les modèles utilisés dans `config/Config.py` :

```python
GROQ_model="llama3-8b-8192"
NomicEmbeddings_model="nomic-embed-text-v1.5"
```

### Ajouter des sources de documents

Pour ajouter des URLs ou modifier les sources de documents, éditez `src/rag/Data_processing.py` :

```python
urls = [
    "votre_url_1",
    "votre_url_2",
    # ...
]
```

## ⚠️ Dépannage

### Erreur de clé API manquante
Assurez-vous que le fichier `.env` est présent à la racine du projet et contient toutes les clés nécessaires.

### Problème avec PyAudio
Sur Windows, installez les outils de build Visual C++ ou utilisez `pipwin` :
```bash
pip install pipwin
pipwin install pyaudio
```

### Erreur CUDA
Si vous n'avez pas de GPU CUDA, modifiez `src/rag/Data_processing.py` ligne 53 :
```python
device="cpu"  # au lieu de "cuda"
```

Et dans `src/audio/Speech_To_Text.py` ligne 84 :
```python
device="cpu"  # au lieu de "cuda"
```

### Problème de chemin / ModuleNotFoundError: No module named 'config'
**Ce problème a été corrigé dans le code**, mais si vous rencontrez toujours cette erreur :
- Assurez-vous d'exécuter les commandes depuis la racine du projet (où se trouve le fichier `README.md`)
- Vérifiez que le dossier `config/` existe à la racine du projet
- Les chemins relatifs utilisent maintenant `__file__` pour être indépendants du répertoire de travail actuel

## 📝 Notes

- La base de données ChromaDB est créée automatiquement lors de la première exécution
- Les documents sont segmentés en chunks pour optimiser la récupération
- L'agent utilise un système de grading pour évaluer la pertinence des documents et des réponses

## 📄 Licence

[Préciser la licence du projet]

## 👤 Auteur

[Votre nom]

---

**Bon usage de l'agent RAG ! 🚀**

