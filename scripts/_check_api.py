from dotenv import load_dotenv
load_dotenv(override=False)
import os
key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
base = os.getenv("OPENAI_BASE_URL")
src = "OPENAI_API_KEY" if os.getenv("OPENAI_API_KEY") else "GITHUB_TOKEN"
print("base_url  :", base)
print("key prefix:", (key[:8] + "...") if key else "NONE")
print("key source:", src)
