import requests
from llamaapi import LlamaAPI
import json
import PyPDF2

def extract_text_from_pdf():
  text = ''

  reader = PyPDF2.PdfReader("update09.pdf")
  number_of_pages = len(reader.pages)


  for i in range(0, number_of_pages):
    page = reader.pages[i]
    text = page.extract_text()
    words = text.split()
    print("** Page", i+1, ", text length", len(text), ", num words", len(words))
    for word in words:
      text += word + ' '
  return text


llama=LlamaAPI('LLAMA_API_KEY')

# API Request JSON Cell
api_request_json = {
  "model": "llama3-70b",
  "messages": [
    {"role": "system", "content": "Who are you?"},
    {"role": "user", "content": "Summarize the following text:" + extract_text_from_pdf()},
  ]
}

# Make your request and handle the response
response = llama.run(api_request_json)
text = response.json()['choices'][0]['message']['content']
print(text)

