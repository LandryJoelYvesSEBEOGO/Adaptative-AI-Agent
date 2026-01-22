import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Ajouter le répertoire racine du projet au sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.rag.Rag_model import get_final_response
from config.Config import Config

# Load environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# Title and description
st.title("💬 Langraph AI Agent: Adaptative RAG 🤖")
st.info("Explore advanced retrieval-augmented generation with our custom RAG model", icon="📚")

# Sidebar for additional info
st.sidebar.title("About the RAG Chatbot")
st.sidebar.markdown("""
### How it Works
- Retrieves relevant documents.
- Make Web search.
- Generates contextually-aware responses.
""")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about AI, ML, or my knowledge base!"}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Input field for new questions
user_input = st.chat_input("Posez une question :")

# Process user input and generate response
if user_input:
    # Add user message to chat history immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Display user message instantly in the chat
    with st.chat_message("user"):
        st.write(user_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        streaming_enabled = getattr(Config, 'STREAMING_ENABLED', True)
        
        if streaming_enabled:
            try:
                # Utiliser streaming
                from src.rag.Rag_model import get_final_response_stream
                response_chunks = []
                message_placeholder = st.empty()
                
                for chunk in get_final_response_stream(user_input):
                    response_chunks.append(chunk)
                    # Afficher progressivement
                    message_placeholder.write("".join(response_chunks))
                
                # Récupérer la réponse complète
                full_response = "".join(response_chunks)
                
                # Ajouter à l'historique
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                # Fallback sur non-streaming
                print(f"⚠️ Erreur streaming, fallback: {str(e)}")
                response = get_final_response(user_input)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            # Génération normale sans streaming
            with st.spinner("Thinking..."):
                try:
                    response = get_final_response(user_input)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_message = f"⚠️ Une erreur s'est produite lors de la génération de la réponse. Veuillez réessayer."
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_message
                    })
                    print(f"❌ Erreur dans main.py: {str(e)}")