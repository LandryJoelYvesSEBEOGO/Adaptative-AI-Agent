import uvicorn
import os 
import sys
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel
#from rag_app.query_rag import QueryResponse, query_rag
Rag_folder_path = os.path.abspath(os.path.join("src", "rag"))
sys.path.append(Rag_folder_path)
from Rag_model import get_final_response
from Rag_model import QueryResponse

app = FastAPI()
handler = Mangum(app)  # Entry point for AWS Lambda.


class SubmitQueryRequest(BaseModel):
    query_text: str


@app.get("/")
def index():
    return {"Hello": "World"}


@app.post("/submit_query")
def submit_query_endpoint(request: SubmitQueryRequest) -> QueryResponse:
    query_response = get_final_response(request.query_text)
    return query_response


if __name__ == "__main__":
    # Run this as a server directly.
    port = 8000
    print(f"Running the FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="0.0.0.0", port=port)