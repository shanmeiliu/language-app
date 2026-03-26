CREATE TABLE prompt (
    prompt_id SERIAL PRIMARY KEY,
    source_lang VARCHAR(20) NOT NULL,
    target_lang VARCHAR(20) NOT NULL,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL
);

CREATE TABLE alternate (
    alternate_id SERIAL PRIMARY KEY,
    prompt_id INT NOT NULL,
    option_text TEXT NOT NULL,
    CONSTRAINT fk_prompt
        FOREIGN KEY(prompt_id)
        REFERENCES prompt(prompt_id)
        ON DELETE CASCADE
);