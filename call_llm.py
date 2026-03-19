from openai import OpenAI
import json
import logging

logging.basicConfig(
    level=logging.ERROR, # Set the minimum level to log (DEBUG and above)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(), # Output to console
        #logging.FileHandler("app.log") # Output to a file
    ]
)
logger = logging.getLogger(__name__) 
def llm_common_call(prompt: str, prompt_file: str) -> str:
    with open('config.json') as f:
        config_data=json.load(f)

    base_url = config_data["baseUrl"]
    token = config_data["token"]
    llm = config_data["model"]
    # Check the key

    if not token:
        logger.error("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
    elif token.strip() != token:
        logger.warning("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
    else:
        logger.info("API key found and looks good so far!")

    file_path = prompt_file
    with open(file_path, 'r') as f1:
        content = f1.read()
    system_prompt = content

    client = OpenAI(api_key=token, base_url=base_url)
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": "You are a helpful language expert." + system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def make_flashcard_for_topic(topic, difficulty, source_lang, dest_lang, num_options, num) -> str:
    prompt_file = './prompts/make_flashcard_for_topic.txt'
    test_prompt = f"""
        {{
        "source_language": {source_lang},
        "target_language": {dest_lang},
        "prompt_type": "phrase",
        "difficulty": {difficulty},
        "topic": {topic},
        "num_options": {num_options}
        "num": {num}
        }}
        """

    return llm_common_call(test_prompt, prompt_file)



print(make_flashcard_for_topic("卑鄙是卑鄙者的通行证，高尚是高尚者的墓志铭", "expert",  "Chinese", "English", 4, 2))



def make_flashcard_for_phrase(phrase, source_lang, dest_lang, num_options, text_type) -> str:
    prompt_file = './prompts/make_flashcard_for_phrase.txt'

    test_prompt_phrase = f"""
        {{
        "source_language": {source_lang},
        "target_language": {dest_lang},
        "source_text": {phrase},
        "num_options": {num_options},
        "text_type": {text_type}
        }}
        """
   
    return llm_common_call(test_prompt_phrase, prompt_file)
   




print(make_flashcard_for_phrase("水至清则无鱼,人至察则无徒", "Chinese", "English", 3, None ))