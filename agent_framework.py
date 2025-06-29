import os
import uuid
import requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_web(query):
    try:
        headers = {"Authorization": f"Bearer {os.getenv('TAVILY_API_KEY')}"}
        json_data = {
            "query": query,
            "search_depth": "advanced",
            "max_results": 3,
            "time_range": "week"
        }
        response = requests.post("https://api.tavily.com/search", headers=headers, json=json_data)
        response.raise_for_status()
        results = response.json()
        content_texts = "\n\n".join([r.get("content", "") for r in results.get("results", [])]).strip()
        return content_texts if content_texts else ""
    except Exception as e:
        print(f"[Search Error] {e}")
        return ""

def summarize(content, language="English"):
    prompt = (
        f"Write a detailed blog post about the following in {language} with relevant source citations:\n\n{content}"
    )
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        return chat_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Summary Error] {e}")
        return ""

def review(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a blog reviewer. Suggest improvements for clarity and engagement."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Review Error] {e}")
        return ""

def tts(text):
    try:
        filename = f"tts_audio_{uuid.uuid4().hex[:8]}.wav"
        audio_folder = os.path.join("static", "audio")
        os.makedirs(audio_folder, exist_ok=True)
        path = os.path.join(audio_folder, filename)
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        with open(path, "wb") as f:
            f.write(speech_response)
        return f"/static/audio/{filename}"
    except Exception as e:
        print(f"[TTS Error] {e}")
        return ""

tools = {
    "search_web": search_web,
    "summarize": summarize,
    "tts": tts,
    "review": review
}

class BlogAgenticAI:
    def __init__(self, query, language="English", tools=None):
        self.query = query
        self.language = language
        self.tools = tools or tools
        self.memory = []
        self.thoughts = [f"My goal is to write a blog on: {self.query}"]

    def generate_blog(self):
        content = self.tools["search_web"](self.query)
        self.thoughts.append("Searched the web for content.")

        if len(content.split()) < 100:
            self.thoughts.append("Insufficient data. Searching more...")
            content += "\n" + self.tools["search_web"](f"More details about {self.query}")

        self.memory.append(("search_results", content))

        summary = self.tools["summarize"](content, language=self.language)
        self.thoughts.append("Generated blog summary.")
        self.memory.append(("blog_summary", summary))

        review_feedback = self.tools["review"](summary)
        self.thoughts.append("Got review feedback.")
        self.memory.append(("review", review_feedback))

        audio_url = self.tools["tts"](summary)
        self.thoughts.append("Created TTS audio.")
        self.memory.append(("audio_url", audio_url))

        return {
            "query": self.query,
            "language": self.language,
            "summary": summary,
            "review_feedback": review_feedback,
            "audio_url": audio_url,
            "thoughts": self.thoughts,
            "memory": self.memory
        }

    def chat_with_ai(self, conversation_history):
        system_msg = {
            "role": "system",
            "content": f"You are an AI assistant knowledgeable about the blog topic '{self.query}'."
        }
        messages = [system_msg] + conversation_history
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
