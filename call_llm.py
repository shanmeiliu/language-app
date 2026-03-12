from openai import OpenAI
import json

def call_llm(prompt: str, language_source: str, language_target: str, llm_model: str) -> str:
    with open('config.json') as f:
        config_data=json.load(f)
    url = config_data["url"]
    base_url = config_data["baseUrl"]
    token = config_data["token"]
    # Check the key

    if not token:
        print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
    elif token.strip() != token:
        print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
    else:
        print("API key found and looks good so far!")

    system_prompt = """


You are given the following configuration in json format:

{
  "source_language": "Spanish",
  "target_language": "English",
  "prompt_type": "word" or "phrase"
  "difficulty": "beginner",
  "topic": "greetings",
  "num_options": 4 
}, 
Note the configuration can all be changed by the user.


And the user want it to return a response like:

{
  "source_language": "Spanish",
  "target_language": "English",
  "source_text": "Hola",
  "target_text": "Hello",
  "options": [
    "Hi",
    "Help",
    "Hole",
    "Hello"
  ],  
}
"""
    client = OpenAI(api_key=token, base_url=base_url)
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "You are a helpful language expert." + system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


test_prompt = """
{
"source_language": "Chinsese",
"target_language": "English",
"prompt_type": "phrase"
"difficulty": "expert",
"topic": "刻舟求剑",
"num_options": 4 
}
"""
print(call_llm(test_prompt, "Chinese", "English", "gemma3:27b"))