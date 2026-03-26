# Connect to an existing database
#conn = psycopg2.connect("dbname=image_ranking user=postgres sslmode=disable host=localhost password=cliu port=5432")
import psycopg2
import uuid
from datetime import datetime




def db_connection(db_connection_string):
    conn = psycopg2.connect(db_connection_string)
    conn.autocommit=True
    return conn.cursor()





# # Open a cursor to perform database operations
# with db_connection() as ocur:
#     ocur.execute("""
#     CREATE TABLE IF NOT EXISTS public.prompt (
#     prompt_id SERIAL PRIMARY KEY,
#     source_lang VARCHAR(20) NOT NULL,
#     target_lang VARCHAR(20) NOT NULL,
#     source_text TEXT NOT NULL,
#     target_text TEXT NOT NULL
# );

# CREATE TABLE IF NOT EXISTS public.alternate (
#     alternate_id SERIAL PRIMARY KEY,
#     prompt_id INT NOT NULL,
#     option_text TEXT NOT NULL,
#     CONSTRAINT fk_prompt
#         FOREIGN KEY(prompt_id)
#         REFERENCES prompt(prompt_id)
#         ON DELETE CASCADE
# );



#     """)

# def create_user(user_id, user_name):
#     with db_connection() as cur:
#         cur.execute("SELECT * FROM public.user WHERE user_id = %s", (user_id,))
#         res=cur.fetchone()
#         if not res:
#             uid = str(uuid.uuid4())
#             # create new user
#             cur.execute("INSERT INTO public.user (id, user_id, user_name, role) VALUES (%s, %s, %s, %s)", (uid, user_id, user_name, -1))
#             return -1
#         else:
#             return res[3]
