from google import genia
import os

os.environment['GEMINI_API_KEY'] = "key_exmaple"
client=genia.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Tell me about marvel"
)
print(response.text)