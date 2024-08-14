import requests
import base64
import json

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def describe_image_claude(prompt):
    API_KEY = "CLAUDE_IMAGE_API_KEY"
    API_URL = "https://api.anthropic.com/v1/messages"
    IMAGE_PATH = "claude_img2.jpeg"
    base64_image = encode_image(IMAGE_PATH)
    payload = {
        "model": "claude-3-sonnet-20240229", 
        "max_tokens": 1000,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
        "anthropic-version": "2023-06-01"
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        print(response.json()['content'][0]['text'])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

describe_image_claude("Describe this image")