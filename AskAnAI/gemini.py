import pathlib
import textwrap

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown
import PyPDF2
import PIL.Image

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


# def to_markdown(text):
#   text = text.replace('•', '  *')
#   return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

google_api_key = "GEMINI_API_KEY"

genai.configure(api_key=google_api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("Summarize this text:" +  extract_text_from_pdf())

print(response.text)

response2 = model.generate_content(["What's in this photo?", PIL.Image.open('gemini_img.png')])

print(response2.text)
