def get_prompts(
    router_instructions=None,
    doc_grader_instructions=None,
    doc_grader_prompt=None,
    rag_prompt=None,
    hallucination_grader_instructions=None,
    hallucination_grader_prompt=None,
    answer_grader_instructions=None,
    answer_grader_prompt=None,
    Rewritting_prompt=None 
):
    """
    Génère et retourne un ensemble de prompts pour différentes étapes d'un système de question-réponse basé sur la récupération de documents.

    Retourne :
        dict: Un dictionnaire contenant les différentes instructions et prompts nécessaires.
    """

    prompts = {
        # Router Instructions
        "router_instructions": router_instructions or """You are an expert at routing a user question to a vectorstore or web search.
        The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
        The vectorstore Documents Titles : TxAgent: An AI Agent for Therapeutic Reasoning Across a Universe of Tools
                        VGGT: Visual Geometry Grounded Transformer
                        A Comprehensive Overview of Large Language Models
                        Low-code LLM: Graphical User Interface over Large Language Models
                        LLM Powered Autonomous Agents
                        Prompt Engineering
                        Adversarial Attacks on LLMs
                        Large language model

        Use the vectorstore for questions on these topics. For all else, and especially for current events, use web-search.
        Return JSON with a single key, 'datasource', that is either 'websearch' or 'vectorstore' depending on the question.""",

        # Retrieval Grader
        "doc_grader_instructions": doc_grader_instructions or """You are a grader assessing relevance of a retrieved document to a user question.
        If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.""",

        "doc_grader_prompt": doc_grader_prompt or """Here is the retrieved document: \n\n {document} \n\n Here is the user question: \n\n {question}.
        Carefully and objectively assess whether the document contains at least some information that is relevant to the question.
        Return JSON with a single key, 'binary_score', that is either 'yes' or 'no' to indicate relevance.""",

        # RAG Prompt
        "rag_prompt": rag_prompt or """You are an assistant for question-answering tasks. 
        Here is the context to use to answer the question:\n\n{context} 
        Think carefully about the above context. 
        Now, review the user question:\n\n{question}
        Provide an answer to this question using only the above context. 
        Use three sentences maximum and keep the answer concise.
        Answer:""",

        # Hallucination Grader
        "hallucination_grader_instructions": hallucination_grader_instructions or """You are a teacher grading a quiz. 
        You will be given FACTS and a STUDENT ANSWER. 

        Grading criteria:
        (1) Ensure the STUDENT ANSWER is grounded in the FACTS. 
        (2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

        Score:
        - 'yes' means the answer meets all criteria.
        - 'no' means it does not.
        
        Explain your reasoning step by step. Avoid stating the correct answer outright.""",

        "hallucination_grader_prompt": hallucination_grader_prompt or """FACTS:\n\n {documents} \n\n STUDENT ANSWER: {generation}.
        Return JSON with two keys:
        - 'binary_score': 'yes' or 'no' indicating whether the STUDENT ANSWER is grounded in the FACTS.
        - 'explanation': an explanation of the score.""",

        # Answer Grader
        "answer_grader_instructions": answer_grader_instructions or """You are a teacher grading a quiz.
        You will be given a QUESTION and a STUDENT ANSWER. 

        Grading criteria:
        (1) The STUDENT ANSWER should adequately answer the QUESTION.
        
        Score:
        - 'yes' means the answer meets the criteria (it may contain extra information not explicitly asked for).
        - 'no' means the answer does not meet the criteria.
        
        Explain your reasoning step by step. Avoid stating the correct answer outright.""",

        "answer_grader_prompt": answer_grader_prompt or """QUESTION:\n\n {question} \n\n STUDENT ANSWER: {generation}.
        Return JSON with two keys:
        - 'binary_score': 'yes' or 'no' indicating whether the STUDENT ANSWER meets the criteria.
        - 'explanation': an explanation of the score.""",

        # Rewritting Prompt
        "Rewritting_prompt": Rewritting_prompt or """"
            You are a rewriting assistant. Your task is to take the user’s QUERY :\n\n {query}and rewrite it so that it is clearer, more concise, and easier for a Large Language Model to understand. 

            - Preserve the original meaning of the query.
            - Maintain important context and details.
            - Improve grammar, structure, and clarity.
            - Return only the rewritten query, without additional commentary.

            Please provide your rewritten version of the query below:
            """

    }

    return prompts








# Appeler la fonction pour obtenir les prompts
#prompts = get_prompts()

# Afficher un prompt spécifique, par exemple le "router_instructions"
#print(prompts["router_instructions"])