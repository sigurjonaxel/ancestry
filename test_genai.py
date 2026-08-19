import os
from PIL import Image
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

for model in ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-flash-latest']:
    try:
        img = Image.new('RGB', (100, 100))
        response = client.models.generate_content(
            model=model,
            contents=[img, "Is this a person?"]
        )
        print(f"{model}: SUCCESS! -> {response.text}")
    except Exception as e:
        print(f"{model}: Error: {e}")
