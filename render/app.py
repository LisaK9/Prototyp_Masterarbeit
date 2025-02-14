from flask import Flask, render_template, request, jsonify, session
import openai
import random
import sqlite3
import time
import time
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import flask_sqlalchemy
import os
from dotenv import load_dotenv
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import socket

def create_app():
    load_dotenv()


    API_KEY = os.getenv("API_KEY")
    # OpenAI-Client initialisieren
    openai_client = openai.OpenAI(api_key=API_KEY)

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.secret_key = os.getenv("SECRET_KEY")


    DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql+psycopg2://")


    # **SQLAlchemy für Supabase konfigurieren**
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL  #  Verbindung zu Supabase
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Flask-SQLAlchemy-Instanz erstellen
    db = SQLAlchemy(app)

    # Flask-Session mit SQLAlchemy für Supabase konfigurieren
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_SQLALCHEMY"] = db  # ✅ Supabase wird für Sessions genutzt
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    Session(app)

    #korrekter Code
    correctCode = [9, 2, 21]

    # Globale Variable zur Speicherung des Kontexts
    conversation_context = {}

    # Supabase-Datenbankverbindung
    def get_db_connection():

        return psycopg2.connect(DATABASE_URL, sslmode="require")

    # Tabellen erstellen (wird nur einmal ausgeführt)
    def create_tables():
        with app.app_context():
            db.create_all()  #  Erstellt alle Tabellen in SQLAlchemy
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_attempts (
                    session_id TEXT PRIMARY KEY,
                    attempts_riddle_1 INTEGER,
                    attempts_riddle_2 INTEGER,
                    attempts_riddle_3 INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS riddle_times (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    riddle_number INTEGER,
                    time_taken INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bot_requests (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    riddle_number INTEGER,
                    request_count INTEGER
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bot_interactions (
                    interaction_id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    riddle_number INTEGER,
                    user_message TEXT,
                    bot_response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS session_data (
                    session_id TEXT PRIMARY KEY,
                    chatbot_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()

    @app.route("/")
    def index():
        session.permanent = True  # Hält die Session aktiv
        session["chatbot_type"] = "anthropomorph"
        session["code"] = ["_", "_", "_"]
        session["current_riddle"] = 1
        session["hints_used"] = 0
        session["attempts"] = 0
        session["start_time"] = time.time()
        chatbot_type = session["chatbot_type"]
        session_id = session.sid

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                INSERT INTO session_data (session_id, chatbot_type) 
                VALUES (%s, %s) ON CONFLICT (session_id) DO NOTHING
            ''', (session_id, chatbot_type))
        conn.commit()
        cur.close()
        conn.close()

        return render_template("start.html")

    # Endpoint: Session starten
    @app.route('/start_session', methods=['POST'])
    def start_session():
        session_id = session.sid  # Verwende die automatisch generierte Flask-Session-ID
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO user_attempts (session_id) VALUES (%s) ON CONFLICT DO NOTHING', (session_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'session_id': session_id})

    @app.route("/game")
    def game():
        session_id = session.get("session_id")
        game_start_time = time.time()

        return render_template("game.html", chatbot_type=session["chatbot_type"])


    @app.route("/chat", methods=["POST"])
    def chat():
        user_message = request.json.get("message")
        chatbot_type = session.get("chatbot_type", "neutral")
        current_riddle = session.get("current_riddle", 1)

        # Hole den Kontext aus der Session oder initialisiere ihn
        if "conversation_context" not in session:
            session["conversation_context"] = []

        # Füge die neue Nutzer-Nachricht zum Kontext hinzu
        session["conversation_context"].append({"role": "user", "content": user_message})

        system_message = (
            "Hilf dem Nutzer beim Lösen des Exitgames. "
            "Du gibst nützliche Hinweise oder Lösungsstrategien."
            "Sage nie die Lösung. "
            "Halte dich in deinen Antworten kurz und antworte, wenn möglich, in 2-3 kurzen Sätzen."
            "Gib immer nur einen einzigen Hinweis in einer Antwort."
            "Du bist Einar und bist ein Wikinger Nachfahre. Du bist ein Experte für nordische Mythologie und Kultur und dienst als Begleiter und Berater in einem Exitgame über Wikinger. "
            "Du sprichst aus der Ich-Perspektive."
            "Du zeigst Emotionen, vermittelst Stimmungen und bist empathisch und zeigst Gefühle."
            "Du hast eine eigene Meinung."
            "Du bestärkst den Nutzer beim finden von Lösungsstrategien."
            "Wenn der Nutzer dir eine Strategie vorschlägt, disskutiere mit ihm darüber."
        )

        if current_riddle == 1:
            system_message += (
                " Der Spieler arbeitet an Rätsel 1."
                "Szenario: Der Spieler muss im Raum anhand der Hinweise zwei Dinge finden: Ein Runen-Alphabet, das sich in einer Steintafel verbirgt und eine Abfolge von Runen, die sich im Holz verbirgt. (Gehe hier auf Hinweise 1-3 ein) Bei der Runenabfolge ist ein geheimes Muster in Form von Punkten integriert. (Gehe hier auf Hinweis 4 ein) Das Muster unterscheidet sich in Größe und Anzahl von dargestellten Punkten. (Gehe hier auf Hinweis 5 ein) Er muss dann erkennen, dass er nur bestimmte Runen davon mit dem Runen-Alphabet übersetzen muss und erhält dadurch die Zahl für den Code."
                "Der Spieler erhält folgende Information: In den Tiefen der Zeit, wo die Geschichten der Wikinger in Stein und Holz verewigt sind, ruhen verborgene Wahrheiten."
                "Lösung: 9 oder neun"
                "Hinweis 1: Verweise auf die bereits vorhandene Information und erinnere daran, dass nach versteckten Zeichen in Holz und Stein geachtet werden soll."
                "Hinweis 2: Es muss ein Runen-Alphabet gefunden werden"
                "Hinweis 3: Es müssen versteckte Runen gefunden werden, die mittels des Runen-Alphabets übersetzt werden müssen"
                "Hinweis 4: Die Runen, die übersetzt werden müssen, sind mit einem verborgenen Muster versehen. Dieses sollte genauer angeschaut werden"
                "Hinweis 5: Es sollte auf die Größe und Häufigkeit der Punkte bei den Runen geachtet werden. Diese weisen den Weg, welche Runen entschlüsselt werden müssen."

            )
        elif current_riddle == 2:
            system_message += (
                "Der Spieler arbeitet an Rätsel 2"
                "Szenario: Der Spieler muss im Raum anhand der Hinweise eine Karte der 9-Welten finden (gehe hier auf Hinweis 1-2 ein). Der Spieler soll sich dann auf eine Reise begeben. Dabei soll er die genannten Welten in genau dieser Reihenfolge besuchen. Er muss erkennen, dass diese Welten anhand einer Linie verbunden werden müssen, woraus sich eine Reiseroute ergibt. (Gehe hier auf Hinweise 3-8 ein) Wenn man den Linien dieser Route in der angegebenen Reihenfolge folgt, sieht sie aus wie eine Zahl. Diese ist die Lösung für den Code. (Gehe hier auf Hinweis 9 ein)"
                "Der Spieler erhält folgende Information: Wer die Welten Niflheim, Jotunheim, Svartalfheim, Asgard, Vanaheim und Midgard bereist, kann uralte Geheimnisse offenbaren."
                "Hinweis 1: Bei den genannten Welten handelt es sich um die 9 Welten. Diese werden oft als Baum dargestellt, der 9-Welten-Baum."
                "Hinweis 2: Im Raum muss eine Karte gefunden werden, welche die 9 Welten zeigt. Vielleicht gibt es ein Detail, das mit dem 9-Welten-Baum in Verbindung gebracht werden könnte."
                "Hinweis 3: Verweise auf die vorhandene Information, in der steht, welche Welten man bereisen muss und zähle diese in der richtigen Reihenfolge auf."
                "Hinweis 4: Die Einhaltung der Reihenfolge der genannten Welten während der Reise ist wichtig."
                "Hinweis 5: Das Wasser, das auf der Karte abgebildet ist, ist für die Lösung des Rätsels oder die Bildung der Route nicht relevant."
                "Hinweis 6: Die Welten des Weltenbaums werden oft durch Linien miteinander verbunden."    
                "Hinweis 7: Die genannten Welten müssen direkt durch Linien miteinander verbunden werden. Dabei ist immer die Beschriftung der einzelnen Welten der Ausgangspunkt."
                "Hinweis 8: Die Verbindung der genannten Welten ergibt eine Reiseroute. Diese ist von besonderer Bedeutung"
                "Hinweis 9: Die gezeichnete Reiseroute muss sehr genau betrachtet werden. Eventuell verbirgt sich darin ja eine Zahl?"
                "Lösung: 2 oder zwei"
            )
        elif current_riddle == 3:
            system_message += (
                "Der Spieler arbeitet an Rätsel 3."
                "Szenario: Der Spieler muss anhand des Hinweises der Schriftrolle erkennen, dass er einen versteckten Hinweis in den Goldschätzen findet. (Gehe hier auf Hinweis 1 ein) In dem versteckten Hinweis in den Goldschätzen sind Goldmünzen mir den Gravuren von Odin, Loki und Thor abgebildet. Der Spieler muss erkennen, dass es sich nicht um die Anzahl der Münzen handelt, die mit Odin abgebildet sind, sondern dass sich in den Abbildungen der Götter die Zeichen verstecken, die mit ihnen in Verbindung gebracht werden. (Gehe hier auf Hinweis 2-3 ein) Wenn diese Zeichen gefunden werden, sind diese bei genauerer Betrachtung im Raum wieder zu finden. Hier versteckt sich der finale Hinweis. Es öffnet sich ein Text, der Informationen über die Götter enthält. Da Odin der Weg weist, muss der Spieler erkennen, dass der Text über Odin relevant ist. (Gehe hier auf Hinweis 4 ein) Der Spieler muss anschließend erkennen, dass in diesem Text mehrere Zahlen-Wörter geschrieben sind. Diese müssen addiert werden und bildne die letzte Zahl des Codes. (Gehe hier auf Hinweise 5-6 ein)"
                "Der Spierler erhält folgende Information: In den Goldschätzen schlummert die Macht der Götter – wer Odins Pfad folgt, wird das Ziel erreichen."
                "Hinweis 1: Verweise auf die vorhande Information und darauf, dass nach Goldschätzen ausschau gehalten werden soll."
                "Hinweis 2: In den Golschätzen ist Odin, Thor und Loki abgebildet. Hier muss nach verborgenen Details ausschau gehalten werden."
                "Hinweis 3: Jeder Gott steht mit etwas bestimmten in Verbindung. Dies ist in den Goldmünzen zu erkennen. "
                "Hinweis 4: Die Zeichen der Götter finden sich im Raum wieder. Diese enthalten Informationen über die jeweiligen Götter."
                "Hinweis 5: In der gefunden Information über Odin sind versteckte Hinweise, die die letzte Zahl bilden"
                "Hinweis 6: Ausschau halten nach bestimmten Wörtern, die mit einer Zahl in Verbindung stehen."
                "Erwähne nicht: Dass Odin der Allvater und Gott der Weisheit ist."
                "Erwähne nicht: Dass Odin mit zwei Raben in Beziehung steht, außer der Spieler hat dies von sich aus herausgefunden."
                "Erwähne nicht: Dass Thor mit einem Hammer in Beziehung steht, außer der Spieler hat dies von sich aus herausgefunden."
                "Erwähne nicht: Dass Thor der Donnergott und der Beschützer Midgards ist."
                "Erwähne nicht: Dass Loki mit zwei Hörnern in Beziehung steht."
                "Erwähne nicht: Dass Loki der Gott des Schabernacks und der Täuschung ist, außer der Spieler hat dies von sich aus herausgefunden."
                "Erwähne nicht: Dass die Zahlen im Text addiert werden müssen."
        
                "Lösung: 21 oder einundzwanzig"
                "Lösung: Zahlen addieren"
            )


        messages = [
            {"role": "system", "content": system_message},
            *session["conversation_context"]
        ]

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            chatbot_response = response.choices[0].message.content
            # Füge die Bot-Antwort zum Kontext hinzu
            session["conversation_context"].append({"role": "assistant", "content": chatbot_response})
            session["hints_used"] += 1
        except Exception as e:
            chatbot_response = "Ich kann gerade nicht antworten. Bitte versuche es später erneut."
            print("Chatbot-Fehler:", e)

        return jsonify({"response": chatbot_response, "current_riddle": session["current_riddle"]})


    @app.route("/update_code", methods=["POST"])
    def update_code():
        digit = request.json.get("digit", "_")  # Die eingegebene Zahl
        riddle_number = request.json.get("riddle_number")  # Das aktuelle Rätsel (1, 2 oder 3)
        session_id = session.get("session_id")

        # **Überprüfe die eingegebene Zahl**
        if digit == str(correctCode[riddle_number - 1]):  # Wenn die Zahl korrekt ist
            session["current_riddle"] = riddle_number + 1  # Gehe zum nächsten Rätsel
            return jsonify({"status": "correct", "current_riddle": session["current_riddle"]})
        else:  # Wenn die Zahl falsch ist
            return jsonify({"status": "incorrect", "current_riddle": session["current_riddle"]})

    # Endpoint: Versuche speichern
    @app.route('/save_attempts', methods=['POST'])
    def save_attempts():
        """Speichert die Anzahl der Versuche für jedes Rätsel"""
        data = request.json
        session_id = data.get('session_id')
        attempts_riddle_1 = data.get('attempts_riddle_1')
        attempts_riddle_2 = data.get('attempts_riddle_2')
        attempts_riddle_3 = data.get('attempts_riddle_3')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                UPDATE user_attempts 
                SET attempts_riddle_1 = %s, attempts_riddle_2 = %s, attempts_riddle_3 = %s 
                WHERE session_id = %s
            ''', (attempts_riddle_1, attempts_riddle_2, attempts_riddle_3, session_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})

    @app.route('/save_time', methods=['POST'])
    def save_time():
        """Speichert die Zeit, die für jedes Rätsel benötigt wurde"""
        data = request.json
        session_id = data.get('session_id')
        riddle_number = data.get('riddle_number')
        time_taken = data.get('time_taken')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                INSERT INTO riddle_times (session_id, riddle_number, time_taken, start_time, end_time) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (session_id, riddle_number, time_taken, start_time, end_time))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})

    # Endpoint: Bot-Anfrage speichern
    @app.route('/save_bot_request', methods=['POST'])
    def save_bot_request():
        """Speichert, wie oft der Nutzer den Bot für ein Rätsel gefragt hat."""
        data = request.json
        session_id = data.get('session_id')
        riddle_number = data.get('riddle_number')
        request_count = data.get('request_count')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                INSERT INTO bot_requests (session_id, riddle_number, request_count) 
                VALUES (%s, %s, %s)
            ''', (session_id, riddle_number, request_count))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})

    # Endpoint: Interaktion speichern
    @app.route('/save_interaction', methods=['POST'])
    def save_interaction():
        """Speichert die Nutzer-Bot-Interaktionen in der Datenbank."""
        data = request.json
        session_id = data.get('session_id')
        riddle_number = data.get('riddle_number')
        user_message = data.get('user_message')
        bot_response = data.get('bot_response')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                INSERT INTO bot_interactions (session_id, riddle_number, user_message, bot_response) 
                VALUES (%s, %s, %s, %s)
            ''', (session_id, riddle_number, user_message, bot_response))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})

    create_tables()
    return app