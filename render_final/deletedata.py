import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("POOL_DATABASE_URL").replace("postgres://", "postgresql+psycopg2://")

# Verbindung zur Datenbank
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

# Tabellen löschen
cur.execute("""
    DROP TABLE IF EXISTS 
        user_attempts, 
        riddle_times, 
        bot_requests, 
        bot_interactions, 
        session_data, 
        verification,
        survey,
        viewed_solutions,
        user_attempts_n, 
        riddle_times_n, 
        bot_requests_n, 
        bot_interactions_n, 
        session_data_n, 
        verification_n,
        survey_n,
        viewed_solutions_n,
        sessions,
        solutions_n,
        survey_results_n,
        user_codes,
        verification_codes,
        verification_codes_n
    CASCADE;
""")

conn.commit()
cur.close()
conn.close()

print("Alle Tabellen wurden gelöscht.")
