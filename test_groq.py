
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY not found in .env")
else:
    try:
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0
        )

        response = llm.invoke(
            "Explain what an erasure request means in one sentence."
        )

        print("\nGROQ API CONNECTED SUCCESSFULLY!")
        print("\nLLM RESPONSE:")
        print(response.content)

    except Exception as e:
        print("GROQ API ERROR:", e)
