# 🤖 Modèle RAG avec Recherche Web et Reranking

## 📝 Description
Ce projet implémente un système de RAG (Retrieval-Augmented Generation) avancé utilisant un modèle de reranking pour améliorer la pertinence des réponses. L'interface utilisateur est construite avec Streamlit, offrant une expérience utilisateur intuitive et moderne.

## 🎥 Démonstration
[![Démonstration du Modèle RAG](AI%20Agent_Images/Langrah+Adaptative+RAG+model.mp4)](AI%20Agent_Images/Langrah+Adaptative+RAG+model.mp4)

## 📸 Captures d'écran
### Interface Utilisateur
![Interface Utilisateur](AI%20Agent_Images/1.jpg)

### Résultats de Recherche
![Résultats de Recherche](AI%20Agent_Images/2.jpg)

## ✨ Fonctionnalités
- 🔍 Recherche web intégrée
- 🧠 Modèle RAG avec reranking
- 🎨 Interface utilisateur moderne et responsive
- 🔒 Gestion sécurisée des clés API
- 📊 Affichage des résultats en temps réel

## 🛠️ Technologies Utilisées
- Python 3.x
- Streamlit
- Modèles de reranking
- API de recherche web

## 🚀 Installation

1. Clonez le repository :
```bash
git clone [URL_DU_REPO]
cd [NOM_DU_DOSSIER]
```

2. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurez vos variables d'environnement :
```bash
cp .env.example .env
# Éditez le fichier .env avec vos clés API
```

## 💻 Utilisation

1. Lancez l'application :
```bash
streamlit run main.py
```

2. Ouvrez votre navigateur à l'adresse : `http://localhost:8501`

3. Entrez votre requête dans la zone de texte et cliquez sur "Rechercher"

## 🔒 Sécurité
- Les clés API sont stockées dans le fichier `.env`
- Le fichier `.env` est exclu du contrôle de version
- Utilisez `.env.example` comme modèle pour configurer vos variables d'environnement

## 📁 Structure du Projet
```
.
├── main.py              # Application principale Streamlit
├── Rag_model.py         # Implémentation du modèle RAG
├── requirements.txt     # Dépendances du projet
├── .env.example        # Modèle de configuration
├── AI Agent_Images/    # Dossier contenant les médias
└── README.md           # Documentation
```

## 🤝 Contribution
Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👥 Auteurs
- [Votre Nom]

## 📞 Support
Pour toute question ou problème, veuillez ouvrir une issue dans le repository GitHub. 