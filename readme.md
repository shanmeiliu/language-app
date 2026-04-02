# Language Learning Flashcard App (LLM + Postgres)

A Python-based language learning tool that generates multiple-choice flashcards using an LLM and stores them in PostgreSQL with a cache-first retrieval strategy.

---

## ✨ Features

* Generate flashcards from:

  * 📌 Topic-based prompts
  * 🧩 Phrase/idiom inputs
* Multiple-choice questions with plausible distractors
* Structured JSON output enforced via prompt templates
* Automatic database persistence
* Cache-first lookup to avoid repeated LLM calls
* Response sanitization to handle malformed LLM outputs
* Transaction-safe database operations

---

## 🧠 How It Works

```text
User Request
     ↓
Check PostgreSQL (cache)
     ↓
 ┌───────────────┐
 │ Found in DB   │ → Return instantly
 └───────────────┘
     ↓ (miss)
Call LLM → Generate Flashcard
     ↓
Sanitize + Parse JSON
     ↓
Save to DB
     ↓
Return Result
```

---

## 🗄️ Database Schema

### `flashcard`

Stores the main learning item.

* `flashcard_id` (UUID)
* `source_lang`
* `target_lang`
* `prompt_type` (phrase | topic)
* `text_type`
* `difficulty`
* `topic`
* `source_text`
* `target_text`
* `explanation`
* `created_at`

---

### `flashcard_option`

Stores multiple-choice options.

* `option_id` (UUID)
* `flashcard_id` (FK)
* `option_text`
* `is_correct`
* `option_order`

---

### `generation_run`

Stores LLM metadata.

* `run_id` (UUID)
* `flashcard_id` (FK)
* `model_name`
* `prompt_template`
* `raw_request`
* `raw_response`
* `created_at`

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install openai psycopg
```

---

### 2. Create PostgreSQL database

Create a database manually (e.g., `language_db`).

Tables will be created automatically when the app runs.

---

### 3. Create `config.json`

```json
{
  "baseUrl": "https://api.openai.com/v1",
  "token": "YOUR_API_KEY",
  "model": "gpt-4o-mini",
  "db_connection_string": "postgresql://user:password@localhost:5432/language_db"
}
```

---

## ▶️ Run the App

```bash
python call_llm.py
```

### First run:

* Tables are created automatically
* Flashcards are generated via LLM

### Subsequent runs:

* Existing flashcards are retrieved from DB (no LLM call)

---

## 📁 Project Structure

```text
.
├── call_llm.py
├── config.json
├── database/
│   └── db_helper.py
├── prompts/
│   ├── make_flashcard_for_phrase.txt
│   └── make_flashcard_for_topic.txt
```

---

## 🧩 Prompt Design

Prompt templates enforce strict JSON output:

* No markdown
* No extra text
* Fixed schema
* Includes explanation + distractors

This ensures reliable parsing and storage.

---

## 🧹 LLM Response Handling

Responses are sanitized to remove:

* ```json code fences
  ```
* extra text before/after JSON

Then parsed safely before saving.

---

## ⚡ Cache Strategy

Before calling the LLM, the app checks:

* Phrase requests → match by language, text_type, and source_text
* Topic requests → match by language, topic, difficulty, text_type

If a match is found:

* Return from DB immediately

If not:

* Call LLM → save → return

---

## 🔒 Transaction Safety

Database operations use a context manager:

* Auto commit on success
* Auto rollback on failure
* No connection leaks

---

## 🚀 Future Improvements

* Request hashing for exact cache matching
* Input/output validation layer
* Retry logic for invalid LLM responses
* FastAPI interface for serving flashcards
* pgvector integration for semantic search
* User progress tracking

---

## 📌 Example Output

```json
{
  "source_language": "Chinese",
  "target_language": "English",
  "prompt_type": "phrase",
  "text_type": "idiom",
  "difficulty": "intermediate",
  "topic": null,
  "source_text": "守株待兔",
  "target_text": "wait idly for opportunities",
  "explanation": "Describes someone who waits passively instead of taking action.",
  "options": [
    "wait idly for opportunities",
    "work steadily toward success",
    "hide the truth from others",
    "make a decision too quickly"
  ]
}
```

---

## 🧑‍💻 Notes

* Python 3.10+ recommended
* PostgreSQL required
* Uses `psycopg` (v3) for database connectivity
* Designed for extensibility into a full learning system
