import streamlit as st
import requests
from typing import Optional
from Rag_model import get_final_response

class RGSearchInterface:
    def __init__(self):
        # Configuration de base de l'interface
        st.set_page_config(page_title="Modèle RG avec Recherche Web", page_icon="🔍")
        
        # Style CSS personnalisé
        st.markdown("""
        <style>
        .main-container {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
        }
        .stTextInput > div > div > input {
            border: 2px solid #3498db;
            border-radius: 5px;
            padding: 10px;
        }
        .stButton > button {
            background-color: #2ecc71;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stButton > button:hover {
            background-color: #27ae60;
        }
        .result-box {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    def perform_web_search(self, query: str) -> Optional[dict]:
        """
        Effectue une recherche web (à remplacer avec votre logique de recherche)
        """
        try:
            # Exemple de simulation de recherche web
            response=get_final_response(query)

            # Remplacez ceci par votre véritable mécanisme de recherche
            return {
                "query": query,
                "results": [
                    "Résultat 1 pour " + response,
                    "Résultat 2 pour " + response
                ]
            }
        except Exception as e:
            st.error(f"Erreur de recherche : {e}")
            return None

    def process_query(self, query: str):
        """
        Traite la requête avec le modèle RG
        """
        # Placeholder pour votre logique de modèle RG
        return f"Réponse générée pour : {query}"

    def run(self):
        """
        Interface principale Streamlit
        """
        st.title("🤖 Interface de Recherche RG")
        
        # Conteneur principal
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Zone de saisie de la requête
        query = st.text_input("Posez votre question", placeholder="Entrez votre requête ici...")
        
        # Bouton de soumission
        if st.button("Rechercher"):
            if query:
                # Traitement de la requête
                rg_response = self.process_query(query)
                
                # Recherche web conditionnelle
                web_results = self.perform_web_search(query)
                
                # Affichage des résultats
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                
                # Réponse du modèle RG
                st.subheader("Réponse du Modèle")
                st.write(rg_response)
                
                # Résultats de recherche web
                if web_results:
                    st.subheader("Résultats Web")
                    for result in web_results.get('results', []):
                        st.info(result)
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("Veuillez entrer une requête")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        



# Exécution de l'interface
if __name__ == "__main__":
    interface = RGSearchInterface()
    interface.run()