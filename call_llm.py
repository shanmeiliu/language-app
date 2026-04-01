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

def get_flashcard_by_id(db_connection_string: str, flashcard_id: str) -> dict | None:
    with db_connection(db_connection_string) as cur:
        cur.execute(
            """
            SELECT
                flashcard_id,
                source_lang,
                target_lang,
                prompt_type,
                text_type,
                difficulty,
                topic,
                source_text,
                target_text,
                explanation,
                created_at
            FROM public.flashcard
            WHERE flashcard_id = %s
            """,
            (flashcard_id,),
        )
        row = cur.fetchone()

        if not row:
            return None

        cur.execute(
            """
            SELECT option_text, is_correct, option_order
            FROM public.flashcard_option
            WHERE flashcard_id = %s
            ORDER BY option_order ASC
            """,
            (flashcard_id,),
        )
        options = cur.fetchall()

    return {
        "flashcard_id": row[0],
        "source_language": row[1],
        "target_language": row[2],
        "prompt_type": row[3],
        "text_type": row[4],
        "difficulty": row[5],
        "topic": row[6],
        "source_text": row[7],
        "target_text": row[8],
        "explanation": row[9],
        "created_at": row[10].isoformat() if row[10] else None,
        "options": [
            {
                "text": opt[0],
                "is_correct": opt[1],
                "order": opt[2],
            }
            for opt in options
        ],
    }

def find_existing_phrase_flashcard(
    db_connection_string: str,
    source_lang: str,
    target_lang: str,
    text_type,
    source_items: list[str],
):
    with db_connection(db_connection_string) as cur:
        cur.execute(
            """
            SELECT flashcard_id
            FROM public.flashcard
            WHERE source_lang = %s
              AND target_lang = %s
              AND prompt_type = 'phrase'
              AND text_type IS NOT DISTINCT FROM %s
              AND source_text = ANY(%s)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (source_lang, target_lang, text_type, source_items),
        )
        row = cur.fetchone()

    if not row:
        return None

    return get_flashcard_by_id(db_connection_string, row[0])

def find_existing_topic_flashcard(
    db_connection_string: str,
    source_lang: str,
    target_lang: str,
    topic: str,
    difficulty: str,
    text_type,
):
    with db_connection(db_connection_string) as cur:
        cur.execute(
            """
            SELECT flashcard_id
            FROM public.flashcard
            WHERE source_lang = %s
              AND target_lang = %s
              AND prompt_type = 'topic'
              AND topic = %s
              AND difficulty = %s
              AND text_type IS NOT DISTINCT FROM %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (source_lang, target_lang, topic, difficulty, text_type),
        )
        row = cur.fetchone()

    if not row:
        return None

    return get_flashcard_by_id(db_connection_string, row[0])

def flashcard_record_to_response(record: dict) -> dict:
    return {
        "source_language": record["source_language"],
        "target_language": record["target_language"],
        "prompt_type": record["prompt_type"],
        "text_type": record["text_type"],
        "difficulty": record["difficulty"],
        "topic": record["topic"],
        "source_text": record["source_text"],
        "target_text": record["target_text"],
        "explanation": record["explanation"],
        "options": [opt["text"] for opt in record["options"]],
    }
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

def get_or_create_topic_flashcard(
    db_connection_string: str,
    model_name: str,
    topic,
    difficulty,
    source_lang,
    dest_lang,
    num_options,
    num,
    text_type="phrase",
) -> dict:
    existing = find_existing_topic_flashcard(
        db_connection_string=db_connection_string,
        source_lang=source_lang,
        target_lang=dest_lang,
        topic=topic,
        difficulty=difficulty,
        text_type=text_type,
    )

    if existing:
        print("Topic flashcard found in DB cache.")
        return flashcard_record_to_response(existing)

    print("Topic flashcard not found in DB. Calling LLM...")

    raw_response = make_flashcard_for_topic(
        topic=topic,
        difficulty=difficulty,
        source_lang=source_lang,
        dest_lang=dest_lang,
        num_options=num_options,
        num=num,
        text_type=text_type,
    )

    sanitized_response = sanitize_llm_json_response(raw_response)
    card_data = json.loads(sanitized_response)

    flashcard_id = save_flashcard(
        db_connection_string=db_connection_string,
        card_data=card_data,
        model_name=model_name,
        prompt_template="./prompts/make_flashcard_for_topic.txt",
        raw_request={
            "source_language": source_lang,
            "target_language": dest_lang,
            "difficulty": difficulty,
            "topic": topic,
            "num_options": num_options,
            "num": num,
            "text_type": text_type,
        },
        raw_response=sanitized_response,
    )

    saved = get_flashcard_by_id(db_connection_string, flashcard_id)
    return flashcard_record_to_response(saved)

def get_or_create_phrase_flashcard(
    db_connection_string: str,
    model_name: str,
    phrase_array,
    source_lang,
    dest_lang,
    num_options,
    text_type,
) -> dict:
    existing = find_existing_phrase_flashcard(
        db_connection_string=db_connection_string,
        source_lang=source_lang,
        target_lang=dest_lang,
        text_type=text_type,
        source_items=phrase_array,
    )

    if existing:
        print("Phrase flashcard found in DB cache.")
        return flashcard_record_to_response(existing)

    print("Phrase flashcard not found in DB. Calling LLM...")

    raw_response = make_flashcard_for_phrase(
        phrase_array=phrase_array,
        source_lang=source_lang,
        dest_lang=dest_lang,
        num_options=num_options,
        text_type=text_type,
    )

    sanitized_response = sanitize_llm_json_response(raw_response)
    card_data = json.loads(sanitized_response)

    flashcard_id = save_flashcard(
        db_connection_string=db_connection_string,
        card_data=card_data,
        model_name=model_name,
        prompt_template="./prompts/make_flashcard_for_phrase.txt",
        raw_request={
            "source_items": phrase_array,
            "source_language": source_lang,
            "target_language": dest_lang,
            "num_options": num_options,
            "text_type": text_type,
        },
        raw_response=sanitized_response,
    )

    saved = get_flashcard_by_id(db_connection_string, flashcard_id)
    return flashcard_record_to_response(saved)


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

    try:
        topic_result = get_or_create_topic_flashcard(
            db_connection_string=db_connection_string,
            model_name=llm,
            topic="classical literature",
            difficulty="advanced",
            source_lang="Chinese",
            dest_lang="English",
            num_options=4,
            num=1,
            text_type="phrase",
        )

        print("Topic result:")
        print(json.dumps(topic_result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        logger.error(f"Topic response was not valid JSON; not saved to DB. Error: {e}")
    except Exception as e:
        logger.error(f"Failed to get or create topic flashcard: {e}")

    try:
        phrase_result = get_or_create_phrase_flashcard(
            db_connection_string=db_connection_string,
            model_name=llm,
            phrase_array=["水至清则无鱼,人至察则无徒", "乌合之众", "守株待兔", "杞人忧天"],
            source_lang="Chinese",
            dest_lang="English",
            num_options=4,
            text_type="idiom",
        )

        print("Phrase result:")
        print(json.dumps(phrase_result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        logger.error(f"Phrase response was not valid JSON; not saved to DB. Error: {e}")
    except Exception as e:
        logger.error(f"Failed to get or create phrase flashcard: {e}")





if __name__ == "__main__":
    main()
