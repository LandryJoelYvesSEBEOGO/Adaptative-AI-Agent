# Import necessary libraries
import os 
import sys
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langgraph.graph import StateGraph, END
from IPython.display import Image, display
from langchain.schema import Document
rag_module_path = os.path.abspath("config")
sys.path.append(rag_module_path)
from Config import Config
Rag_folder_path = os.path.abspath(os.path.join("src", "rag"))
sys.path.append(Rag_folder_path)
from Prompts import get_prompts
from Data_processing import get_retriever
import json
import operator
from typing import List, Annotated, Dict
from typing_extensions import TypedDict
from dataclasses import dataclass
from typing import List
# Load environment variables
load_dotenv()

# Initialize the necessary components
local_llm = ChatGroq(
    model_name=Config.GROQ_model,
    temperature=0,
    groq_api_key=Config.GROQ_API_KEY
)

llm_json_mode = ChatGroq(
    model_name=Config.GROQ_model, 
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}},
    groq_api_key=Config.GROQ_API_KEY
)

retriever = get_retriever()
web_search_tool = TavilySearchResults(k=3, tavily_api_key=Config.TAVILY_API_KEY)

# Load prompts
prompt = get_prompts()




def Rewrite_query(query: str):
    """Rewrite the query to be more specific."""
    print("---Rewrite the query---")
    rewritting_prompt_formatted = prompt["Rewritting_prompt"].format(query=query)
    generation = local_llm.invoke([HumanMessage(content=rewritting_prompt_formatted)])
    # Extract the string if generation is a message object with a .content attribute
    if hasattr(generation, "content"):
        return generation.content
    return generation  # or raise an error if it's not as expected


# Post-processing function for formatting documents
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# GraphState definition
class GraphState(TypedDict):
    question: str
    generation: str
    web_search: str
    max_retries: int
    answers: int
    loop_step: Annotated[int, operator.add]
    documents: List[str]

# Node functions
def retrieve(state: Dict) -> Dict:
    """Retrieve documents from the vector store."""
    print("---RETRIEVE---")
    documents = retriever.invoke(state["question"])
    return {"documents": documents}

def generate(state: Dict) -> Dict:
    """Generate an answer using RAG on the retrieved documents."""
    print("---GENERATE---")
    docs_txt = format_docs(state["documents"])
    rag_prompt_formatted = prompt["rag_prompt"].format(context=docs_txt, question=state["question"])
    generation = local_llm.invoke([HumanMessage(content=rag_prompt_formatted)])
    return {"generation": generation, "loop_step": state.get("loop_step", 0) + 1}

def grade_documents(state: Dict) -> Dict:
    """Grade the relevance of retrieved documents."""
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    filtered_docs = []
    web_search = "No"
    for doc in state["documents"]:
        doc_grader_prompt_formatted = prompt["doc_grader_prompt"].format(document=doc.page_content, question=state["question"])
        result = llm_json_mode.invoke(
            [SystemMessage(content=prompt["doc_grader_instructions"])] +
            [HumanMessage(content=doc_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]
        if grade.lower() == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(doc)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            web_search = "Yes"
    return {"documents": filtered_docs, "web_search": web_search}

#def web_search(state: Dict) -> Dict:
#    """Perform a web search based on the question."""
#    print("---WEB SEARCH---")
#    docs = web_search_tool.invoke({"query": state["question"]})
#    web_results = "\n".join([d["content"] for d in docs])
#    documents = state.get("documents", [])
#    documents.append(Document(page_content=web_results))
#    return {"documents": documents}"""

def web_search(state: Dict) -> Dict:
    """Perform a web search based on the question."""
    print("---WEB SEARCH---")
    results = web_search_tool.invoke({"query": state["question"]})
    documents = state.get("documents", [])

    for res in results:
        content = res["content"]
        url = res.get("url", "No URL provided")
        doc = Document(page_content=content, metadata={"source": url})
        documents.append(doc)

    return {"documents": documents}




# Edge functions
def route_question(state: Dict) -> str:
    """Route the question to either web search or RAG based on LLM decision."""
    print("---ROUTE QUESTION---")
    route_question = llm_json_mode.invoke(
        [SystemMessage(content=prompt["router_instructions"])] +
        [HumanMessage(content=state["question"])]
    )
    source = json.loads(route_question.content)["datasource"]
    return "websearch" if source == "websearch" else "vectorstore"

def decide_to_generate(state: Dict) -> str:
    """Decide whether to generate an answer or add web search."""
    print("---ASSESS GRADED DOCUMENTS---")
    if state["web_search"] == "Yes":
        print("---DECISION: INCLUDE WEB SEARCH---")
        return "websearch"
    else:
        print("---DECISION: GENERATE---")
        return "generate"

def grade_generation_v_documents_and_question(state: Dict) -> str:
    """Grade whether the generation is grounded in the document and answers the question."""
    print("---CHECK HALLUCINATIONS---")
    hallucination_grader_prompt_formatted = prompt["hallucination_grader_prompt"].format(
        documents=format_docs(state["documents"]), generation=state["generation"].content
    )
    result = llm_json_mode.invoke(
        [SystemMessage(content=prompt["hallucination_grader_instructions"])] +
        [HumanMessage(content=hallucination_grader_prompt_formatted)]
    )
    grade = json.loads(result.content)["binary_score"]

    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        answer_grader_prompt_formatted = prompt["answer_grader_prompt"].format(
            question=state["question"], generation=state["generation"].content
        )
        result = llm_json_mode.invoke(
            [SystemMessage(content=prompt["answer_grader_instructions"])] +
            [HumanMessage(content=answer_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]
        return "useful" if grade == "yes" else "not useful"
    elif state["loop_step"] <= state["max_retries"]:
        print("---DECISION: GENERATION IS NOT GROUNDED, RETRYING---")
        return "not supported"
    else:
        print("---DECISION: MAX RETRIES REACHED---")
        return "max retries"

# Workflow definition and graph compilation
workflow = StateGraph(GraphState)
workflow.add_node("websearch", web_search)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

workflow.set_conditional_entry_point(
    route_question,
    {"websearch": "websearch", "vectorstore": "retrieve"},
)
workflow.add_edge("websearch", "generate")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {"websearch": "websearch", "generate": "generate"},
)
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {"not supported": "generate", "useful": END, "not useful": "websearch", "max retries": END},
)

# Compile the graph
graph = workflow.compile()



@dataclass
class QueryResponse:
    query_text: str
    response_text: str
    sources: List[str]

# Final response function
def get_final_response(query: str) -> str:
    """Run the workflow and return the final generated response."""
    query=Rewrite_query(query)
    initial_state = GraphState(question=query)
    final_state = graph.invoke(initial_state)
    #return final_state.get("generation", {}).get("content", "No response generated.")
    generation = final_state.get("generation")

    # Récupération des sources depuis metadata
    documents = final_state.get("documents", [])
    sources = [doc.metadata.get("source", "Unknown source") for doc in documents]

    return QueryResponse(
        query_text=query,
        response_text=generation.content if hasattr(generation, "content") else str(generation),
        sources=sources
    )
