# Notes: Sending Input to AI APIs

For this learning project, we will use a **Gemini model**. AI providers expose different APIs, so the request format depends on which provider you use.

## OpenAI example

The OpenAI Responses API accepts input with the `input` field:

```python
from openai import OpenAI

client = OpenAI()  # Reads OPENAI_API_KEY from the environment
response = client.responses.create(
	model="gpt-4.1-mini",
	input="Explain what a Python function is.",
)
print(response.output_text)
```

## Gemini example

The Gemini API uses `contents` with a role and text parts:

```python
from google import genai

client = genai.Client()  # Reads GEMINI_API_KEY from the environment
response = client.models.generate_content(
	model="gemini-2.5-flash",
	contents="Explain what a Python function is.",
)
print(response.text)
```

## Main idea

- Both examples send text to a model and read generated text from the response.
- The SDK methods, model names, request fields, and response fields differ by provider.
- Keep provider-specific API calls separate in the code so switching providers is easier.

