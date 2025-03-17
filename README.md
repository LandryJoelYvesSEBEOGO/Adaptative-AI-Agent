# 🤖 AI Agent: Adaptive RAG Model with Web Search and Speech-to-Text Entry

## 📝 Description
This project implements an advanced RAG (Retrieval-Augmented Generation) system using LangGraph that is capable of choosing when to perform a web search in order to retrieve additional content and provide a more precise response to a prompt. Built with Streamlit, it offers an intuitive and modern user interface featuring a speech-to-text entry. The system features a modular architecture based on nodes and edges for structured decision-making, as well as hallucination checking and correction, ensuring easier maintenance and scalability.


## 📸 Screenshots
### User Interface
![User Interface](AI%20Agent_Images/1.jpg)

### AI AGENT Workflow
![Search Results](AI%20Agent_Images/2.jpg)

## ✨ Key Features
- 🔍 Integrated web search with dynamic switching between vector and web search
- 🧠 Advanced RAG system with reranking capabilities
- 🎨 Modern and responsive user interface
- 🔒 Secure API key management
- 📊 Real-time results display
- 🎙️ Voice transcription module for generated responses
- 🔄 Automatic hallucination detection and response relevance evaluation
- 🔁 Smart retry system (up to 3 attempts) for quality assurance

## 🛠️ Technologies Used
- Python 3.x
- Streamlit
- LangChain
- Langsmith
- LangGraph
- LLaMA
- Vector Store
- Web Search APIs
- Text-to-Speech APIs
- Embeddings

## 🏗️ Architecture
The system is built on a modular architecture featuring:
- Node and edge-based structure for structured decision-making
- Dynamic scoring system for document relevance evaluation
- Automatic switching between vector search and web search
- Pipeline for hallucination detection and response quality assessment

## 🚀 Installation

1. Clone the repository:
```bash
git clone [REPO_URL]
cd [FOLDER_NAME]
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit the .env file with your API keys
```

## 💻 Usage

1. Launch the application:
```bash
streamlit run main.py
```

2. Open your browser at: `http://localhost:8501`

3. Enter your query in the text area and click "Search"

## 🔒 Security
- API keys are stored in the `.env` file
- `.env` file is excluded from version control
- Use `.env.example` as a template for environment variables

## 📁 Project Structure
```
.
├── main.py              # Main Streamlit application
├── Rag_model.py         # RAG model implementation
├── requirements.txt     # Project dependencies
├── .env.example        # Configuration template
├── AI Agent_Images/    # Media folder
└── README.md           # Documentation
```

## 🤝 Contributing
Contributions are welcome! Please:
1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request



