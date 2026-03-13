from openai import OpenAI
import json

def make_flashcard_for_topic(topic, difficulty, source_lang, dest_lang, model_name: str) -> str:
    with open('config.json') as f:
        config_data=json.load(f)

    base_url = config_data["baseUrl"]
    token = config_data["token"]
    # Check the key

    if not token:
        print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
    elif token.strip() != token:
        print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
    else:
        print("API key found and looks good so far!")

    file_path = './prompts/make_flashcard_for_topic.txt'
    with open(file_path, 'r') as f1:
        content = f1.read()
    system_prompt = content


    test_prompt = f"""
        {{
        "source_language": {source_lang},
        "target_language": {dest_lang},
        "prompt_type": "phrase",
        "difficulty": {difficulty},
        "topic": {topic},
        "num_options": 4 
        }}
        """

    client = OpenAI(api_key=token, base_url=base_url)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful language expert." + system_prompt},
            {"role": "user", "content": test_prompt}
        ]
    )
    return response.choices[0].message.content



print(make_flashcard_for_topic("卑鄙是卑鄙者的通行证，高尚是高尚者的墓志铭", "expert",  "Chinese", "English","gemma3:27b"))



def make_flashcard_for_phrase(phrase, source_lang, dest_lang, model_name: str) -> str:
    with open('config.json') as f:
        config_data=json.load(f)

    base_url = config_data["baseUrl"]
    token = config_data["token"]
    # Check the key

    if not token:
        print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
    elif token.strip() != token:
        print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
    else:
        print("API key found and looks good so far!")

    file_path = './prompts/make_flashcard_for_phrase.txt'
    with open(file_path, 'r') as f1:
        content = f1.read()
    system_prompt = content

    test_prompt_phrase = f"""
        {{
        "source_language": {source_lang},
        "target_language": {dest_lang},
        "source_text": {phrase},
        "num_options": 4
        }}
        """
   
    client = OpenAI(api_key=token, base_url=base_url)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful language expert." + system_prompt},
            {"role": "user", "content": test_prompt_phrase}
        ]
    )
    return response.choices[0].message.content




print(make_flashcard_for_phrase("水至清则无鱼,人至察则无徒", "Chinese", "English", "gemma3:27b"))