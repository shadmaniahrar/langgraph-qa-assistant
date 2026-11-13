import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from typing import TypedDict

# Load local .env file if it exists
load_dotenv()

app = Flask(__name__)

# Fetch API key securely from environment variables
api_key = os.environ.get("OPENROUTER_API_KEY")

# Initialize model using OpenRouter endpoint
model = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    model="nvidia/nemotron-3-ultra-550b-a55b:free",
    api_key=api_key
)

# Define LangGraph State
class LLMState(TypedDict):
    question: str
    answer: str

def llm_qa(state: LLMState) -> LLMState:
    prompt = f"Answer the following question: {state['question']}"
    response = model.invoke(prompt)
    return {"question": state["question"], "answer": response.content}

# Build and compile graph
graph = StateGraph(LLMState)
graph.add_node("llm_qa", llm_qa)
graph.add_edge(START, "llm_qa")
graph.add_edge("llm_qa", END)
workflow = graph.compile()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    # Try getting JSON first, then fallback to form data if JSON fails
    data = request.get_json(silent=True)
    if data and "question" in data:
        user_query = data["question"]
    else:
        user_query = request.form.get("question")
    
    if not user_query:
        return jsonify({"error": "Please enter a question"}), 400
    
    initial_state = {"question": user_query, "answer": ""}
    final_state = workflow.invoke(initial_state)
    
    return jsonify({"answer": final_state["answer"]})
if __name__ == "__main__":
    app.run(debug=True)