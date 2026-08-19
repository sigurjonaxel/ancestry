import os
import google.generativeai as genai
from PIL import Image

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')

try:
    img = Image.new('RGB', (100, 100))
    response = model.generate_content([img, "Is this a person?"])
    print("SUCCESS: " + response.text)
except Exception as e:
    print(f"Error: {e}")
