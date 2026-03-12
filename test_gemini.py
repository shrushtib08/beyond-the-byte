import requests
import json

GEMINI_API_KEY = "AIzaSyDSxVozvJq6FXJAXiohRBojz9Pzbi5iQ_"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

prompt = """
You are a master chef and nutritionist. Provide details for the food item: Chicken Wings.
Respond with ONLY valid, raw JSON (no markdown formatting) using this exact structure:
{
    "prep_time": 0,
    "preparation_steps": [],
    "ingredients": [],
    "nutrition": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "health_benefits": ""}
}
"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}]
}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(GEMINI_URL, json=payload, headers=headers)
    response.raise_for_status()
    response_data = response.json()
    response_text = response_data['candidates'][0]['content']['parts'][0]['text']
    ai_data = json.loads(response_text.strip().replace('```json', '').replace('```', ''))
    print(json.dumps(ai_data, indent=2))
except requests.exceptions.HTTPError as err:
    print(f"HTTP Error: {err.response.text}")
except Exception as e:
    print(f"Error: {e}")
