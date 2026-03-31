from openai import OpenAI
from database.db_helper import db_connection
import uuid
import re
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

def save_flashcard(
    db_connection_string,
    card_data: dict,
    model_name: str,
    prompt_template: str,
    raw_request: dict,
    raw_response: str,
    ) -> str:
    flashcard_id = str(uuid.uuid4())

    with db_connection(db_connection_string) as cur:
        cur.execute(
            """
            INSERT INTO public.flashcard (
                flashcard_id,
                source_lang,
                target_lang,
                prompt_type,
                text_type,
                difficulty,
                topic,
                source_text,
                target_text,
                explanation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                flashcard_id,
                card_data.get("source_language"),
                card_data.get("target_language"),
                card_data.get("prompt_type"),
                card_data.get("text_type"),
                card_data.get("difficulty"),
                card_data.get("topic"),
                card_data.get("source_text"),
                card_data.get("target_text"),
                card_data.get("explanation"),
            ),
        )

        for idx, option in enumerate(card_data.get("options", []), start=1):
            cur.execute(
                """
                INSERT INTO public.flashcard_option (
                    option_id,
                    flashcard_id,
                    option_text,
                    is_correct,
                    option_order
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    flashcard_id,
                    option,
                    option == card_data.get("target_text"),
                    idx,
                ),
            )

        cur.execute(
            """
            INSERT INTO public.generation_run (
                run_id,
                flashcard_id,
                model_name,
                prompt_template,
                raw_request,
                raw_response
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                str(uuid.uuid4()),
                flashcard_id,
                model_name,
                prompt_template,
                json.dumps(raw_request, ensure_ascii=False),
                raw_response,
            ),
        )

    return flashcard_id

def ensure_schema(db_connection_string: str):
    with db_connection(db_connection_string) as cur:
        cur.execute("""
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";

        CREATE TABLE IF NOT EXISTS public.flashcard (
          flashcard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          source_lang VARCHAR(50) NOT NULL,
          target_lang VARCHAR(50) NOT NULL,
          prompt_type VARCHAR(20) NOT NULL,
          text_type VARCHAR(20),
          difficulty VARCHAR(20),
          topic TEXT,
          source_text TEXT,
          target_text TEXT NOT NULL,
          explanation TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS public.flashcard_option (
          option_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          flashcard_id UUID NOT NULL REFERENCES public.flashcard(flashcard_id) ON DELETE CASCADE,
          option_text TEXT NOT NULL,
          is_correct BOOLEAN NOT NULL DEFAULT FALSE,
          option_order INT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS public.generation_run (
          run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          flashcard_id UUID NOT NULL REFERENCES public.flashcard(flashcard_id) ON DELETE CASCADE,
          model_name VARCHAR(100) NOT NULL,
          prompt_template VARCHAR(255) NOT NULL,
          raw_request JSONB,
          raw_response TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """)

def load_config() -> dict:
    with open("config.json") as f:
        return json.load(f)

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
        system_prompt = f1.read()
    

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

    payload = {
        "source_language": source_lang,
        "target_language": dest_lang,
        "difficulty": difficulty,
        "topic": topic,
        "num_options": num_options,
        "num": num,
        "text_type": "phrase"
    }

    test_prompt = json.dumps(payload, ensure_ascii=False)
    return llm_common_call(test_prompt, prompt_file)


def make_flashcard_for_phrase(phrase_array, source_lang, dest_lang, num_options, text_type) -> str:
    prompt_file = './prompts/make_flashcard_for_phrase.txt'

    payload = {
        "source_items": phrase_array,
        "source_language": source_lang,
        "target_language": dest_lang,
        "num_options": num_options,
        "text_type": text_type
    }

    test_prompt_phrase = json.dumps(payload, ensure_ascii=False)
    return llm_common_call(test_prompt_phrase, prompt_file)

def sanitize_llm_json_response(raw_response: str) -> str:
    if not raw_response:
        return raw_response

    text = raw_response.strip()

    # Remove markdown code fences like ```json ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # If the model added extra text before/after the JSON,
    # extract the first complete JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text.strip()


def parse_llm_json_response(raw_response: str) -> dict:
    sanitized = sanitize_llm_json_response(raw_response)
    return json.loads(sanitized)

def main():
    config_data = load_config()
    db_connection_string = config_data["db_connection_string"]
    llm = config_data["model"]

    ensure_schema(db_connection_string)

    # Example 1: topic card
    topic_request = {
        "source_language": "Chinese",
        "target_language": "English",
        "difficulty": "expert",
        "topic": "卑鄙是卑鄙者的通行证，高尚是高尚者的墓志铭",
        "num_options": 4,
        "num": 2,
        "text_type": "phrase"
    }

    raw_topic_response = make_flashcard_for_topic(
        topic=topic_request["topic"],
        difficulty=topic_request["difficulty"],
        source_lang=topic_request["source_language"],
        dest_lang=topic_request["target_language"],
        num_options=topic_request["num_options"],
        num=topic_request["num"]
    )

    print(raw_topic_response)

    try:
        sanitized_topic_response = sanitize_llm_json_response(raw_topic_response)
        print(sanitized_topic_response)

        topic_card = json.loads(sanitized_topic_response)
        topic_flashcard_id = save_flashcard(
            db_connection_string=db_connection_string,
            card_data=topic_card,
            model_name=llm,
            prompt_template="./prompts/make_flashcard_for_topic.txt",
            raw_request=topic_request,
            raw_response=sanitized_topic_response,
        )
        print(f"Saved topic flashcard: {topic_flashcard_id}")
    except json.JSONDecodeError:
        logger.error("Topic response was not valid JSON; not saved to DB.")
    except Exception as e:
        logger.error(f"Failed to save topic flashcard: {e}")

    # Example 2: phrase card
    phrase_request = {
        "source_items": ["水至清则无鱼,人至察则无徒", "乌合之众", "守株待兔", "杞人忧天"],
        "source_language": "Chinese",
        "target_language": "English",
        "num_options": 4,
        "text_type": "idiom"
    }

    raw_phrase_response = make_flashcard_for_phrase(
        phrase_array=phrase_request["source_items"],
        source_lang=phrase_request["source_language"],
        dest_lang=phrase_request["target_language"],
        num_options=phrase_request["num_options"],
        text_type=phrase_request["text_type"]
    )

    print(raw_phrase_response)

    try:
        sanitized_phrase_response = sanitize_llm_json_response(raw_phrase_response)
        print(sanitized_phrase_response)

        phrase_card = json.loads(sanitized_phrase_response)
        phrase_flashcard_id = save_flashcard(
            db_connection_string=db_connection_string,
            card_data=phrase_card,
            model_name=llm,
            prompt_template="./prompts/make_flashcard_for_phrase.txt",
            raw_request=phrase_request,
            raw_response=sanitized_phrase_response,
        )
        print(f"Saved phrase flashcard: {phrase_flashcard_id}")
    except json.JSONDecodeError:
        logger.error("Phrase response was not valid JSON; not saved to DB.")
    except Exception as e:
        logger.error(f"Failed to save phrase flashcard: {e}")


if __name__ == "__main__":
    main()
