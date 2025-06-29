from flask import Flask, request, jsonify, render_template
from agent_framework import BlogAgenticAI, tools

app = Flask(__name__)

# To keep conversation for chat assistant - in-memory store per session or user id in prod
conversation_history = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_blog", methods=["POST"])
def generate_blog():
    data = request.json
    query = data.get("query")
    language = data.get("language", "English")

    if not query:
        return jsonify({"error": "Missing blog topic query"}), 400

    agent = BlogAgenticAI(query=query, language=language, tools=tools)
    result = agent.generate_blog()

    # Reset chat history on new blog generation
    global conversation_history
    conversation_history = []

    return jsonify(result)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "Missing message"}), 400

    global conversation_history
    conversation_history.append({"role": "user", "content": user_message})

    # For demo, fixed query or you could store query in session to persist
    query = data.get("query", "Your blog topic")

    agent = BlogAgenticAI(query=query, tools=tools)
    answer = agent.chat_with_ai(conversation_history)

    conversation_history.append({"role": "assistant", "content": answer})
    return jsonify({"reply": answer})

if __name__ == "__main__":
    app.run()
