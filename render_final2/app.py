from flask import Flask, render_template, request, jsonify, session, flash, url_for, redirect
import openai
import random
import sendgrid
from sendgrid.helpers.mail import Mail
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
import requests
import string
from datetime import datetime, timedelta


def create_app():
    load_dotenv()

    API_KEY = os.getenv("API_KEY")
    # OpenAI-Client initialisieren
    openai_client = openai.OpenAI(api_key=API_KEY)

    # SendGrid API Key
    SENDGRID_API_KEY = os.getenv('API_MAIL')
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.secret_key = os.getenv("SECRET_KEY")

    DATABASE_URL = os.getenv("POOL_DATABASE_URL").replace("postgres://", "postgresql+psycopg2://")

    # SQLAlchemy für Railway
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL + "?sslmode=require"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Flask-SQLAlchemy-Instanz erstellen
    db = SQLAlchemy(app)

    # Flask-Session mit SQLAlchemy
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_SQLALCHEMY"] = db  #
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    Session(app)

    # korrekter Code
    correctCode = [9, 2, 21]

    # Globale Variable zur Speicherung des Kontexts
    conversation_context = {}

    # Supabase-Datenbankverbindung
    def get_db_connection():
        return psycopg2.connect(DATABASE_URL, sslmode="require")

    # Tabellen erstellen
    def create_tables():
        with app.app_context():
            db.create_all()
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
            cur.execute('''
                CREATE TABLE IF NOT EXISTS verification (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                                    CREATE TABLE IF NOT EXISTS survey2 (
                                        id SERIAL PRIMARY KEY,
                                        session_id TEXT,
                                        alter TEXT,
                                        geschlecht TEXT,
                                        bildung TEXT,
                                        exitgame TEXT,
                                        chatbot TEXT,
                                        frage1 INTEGER, frage2 INTEGER, frage3 INTEGER, frage4 INTEGER, frage5 INTEGER,
                                        frage6 INTEGER, frage7 INTEGER, frage8 INTEGER, frage9 INTEGER, frage10 INTEGER,
                                        frage11 INTEGER, frage12 INTEGER, frage13 INTEGER, frage14 INTEGER, frage15 INTEGER, feedback TEXT,
                                        loesungsweg TEXT,
                                        kommunikation TEXT,
                                        interaktion TEXT,
                                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                ''')
            cur.execute('''
                            CREATE TABLE IF NOT EXISTS viewed_solutions (
                                id SERIAL PRIMARY KEY,
                                session_id TEXT NOT NULL,
                                riddle_number INTEGER NOT NULL,
                                viewed BOOLEAN DEFAULT FALSE,
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                CONSTRAINT un_session_riddle UNIQUE (session_id, riddle_number)
                            )
                        ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS hint_clicks (
                    session_id TEXT,
                    hint_number INTEGER,
                    click_count INTEGER DEFAULT 1,
                    PRIMARY KEY (session_id, hint_number)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS viewed_solution_steps (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    riddle_number INTEGER NOT NULL,
                    step_number INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT unique_step_per_session UNIQUE (session_id, riddle_number, step_number)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS used_strategies (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            cur.close()
            conn.close()

    # Funktion zur Generierung eines Verifizierungscodes

    def generate_verification_code():
        return ''.join(random.choices(string.digits, k=6))

    # Route für die E-Mail-Verifizierung

    @app.route('/verify_email', methods=['GET', 'POST'])
    def verify_email():
        if request.method == 'POST':
            email = request.form['email']
            code = generate_verification_code()
            session['email'] = email

            # Session initialisieren, falls noch nicht geschehen
            if 'initialized' not in session:
                session['initialized'] = True
            session_id = session.sid

            # Code, die E-Mail und die Session-ID in der Datenbank speichern
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO verification (email, code, session_id) VALUES (%s, %s, %s)',
                            (email, code, session_id))
            conn.commit()
            cur.close()
            conn.close()

            # E-Mail mit SendGrid versenden
            message = Mail(
                from_email='exitgame_masterarbeit@web.de',
                to_emails=email,
                subject='Dein Bestätigungscode',
                plain_text_content=f'Dein Bestätigungscode lautet: {code}'
            )
            try:
                response = sg.send(message)
                flash('Ein Bestätigungscode wurde an deine E-Mail-Adresse gesendet. Bitte überprüfe auch deinen SPAM-Ordner.')
            except Exception as e:
                flash('Fehler beim Senden der E-Mail. Bitte versuche es später erneut.')
                print(str(e))

            return redirect(url_for('verify_code'))

        return render_template('index_verify.html')

    # Route für die Code-Verifizierung
    @app.route('/verify_code', methods=['GET', 'POST'])
    def verify_code():
        if request.method == 'POST':
            email = request.form['email']
            code = request.form['code']
            session_id = session.sid  # aktuelle Session-ID

            # Code und die Session-ID in der Datenbank prüfen
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                                SELECT code FROM verification 
                                WHERE email = %s AND session_id = %s 
                                ORDER BY created_at DESC LIMIT 1
                            ''', (email, session_id))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result and result[0] == code:
                session['verified'] = True  # Verifizierungsstatus in der Session
                flash('E-Mail erfolgreich verifiziert!')
                return redirect(url_for('index'))
            else:
                flash('Ungültiger Bestätigungscode. Bitte versuche es erneut.')
        else:
            email = session.get('email', '')

        return render_template('verify.html', email=email)


    @app.route("/")
    def index():
        # Überprüfen, ob der Benutzer verifiziert ist
        if not session.get('verified'):
            return redirect(url_for('verify_email'))  # Weiterleitung zur Verifizierung
        if session.get("survey_completed"):
            return render_template('danke.html')
        session.permanent = True  # Hält die Session aktiv
        session["chatbot_type"] = "neutral"
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
        session_id = session.sid
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO user_attempts (session_id) VALUES (%s) ON CONFLICT DO NOTHING', (session_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'session_id': session_id})

    @app.route("/game")
    def game():
        if session.get("game_finished"):
            return render_template("geheimnis.html")
        if session.get("survey_completed"):
            return render_template('danke.html')

        return render_template("game.html", chatbot_type=session["chatbot_type"])

    @app.route('/view_solution', methods=['POST'])
    def view_solution():
        """Speichert, ob der Nutzer die Lösung für ein Rätsel angeschaut hat."""
        data = request.json
        session_id = data.get('session_id')
        riddle_number = data.get('riddle_number')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                    INSERT INTO viewed_solutions (session_id, riddle_number, viewed) 
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (session_id, riddle_number) 
                    DO UPDATE SET viewed = TRUE
                ''', (session_id, riddle_number))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Solution viewed status updated'})

    # Neue Route für die Erfolgsseite
    @app.route("/geheimnis")
    def geheimnis():
        session["game_finished"] = True
        return render_template("geheimnis.html")

    @app.route("/survey")
    def survey():
        if session.get("survey_completed"):
            return render_template('danke.html')
        return render_template("survey.html")

    @app.route("/submit_survey", methods=["POST"])
    def submit_survey():
        session_id = session.sid

        # Demografische Daten
        alter = request.form.get("alter")
        geschlecht = request.form.get("geschlecht")
        bildung = request.form.get("bildungsstand")
        exitgame = request.form.get("exitgame_erfahrung")
        chatbot = request.form.get("chatbot_nutzung")

        # Likert-Fragen (1–20)
        likert_responses = [request.form.get(f"frage{i}") for i in range(1, 16)]

        # Freitextantworten
        feedback = request.form.get("feedback")
        loesungsweg = request.form.get("vorgehen")
        kommunikation = request.form.get("kommunikation")
        interaktion = request.form.get("interaktion")

        conn = get_db_connection()
        cur = conn.cursor()

        # SQL-Insert
        cur.execute(f'''
                INSERT INTO survey2 (
                    session_id, alter, geschlecht, bildung, exitgame, chatbot,
                    {', '.join([f"frage{i}" for i in range(1, 16)])},
                    feedback, loesungsweg, kommunikation, interaktion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    {', '.join(['%s'] * 15)},
                    %s, %s, %s, %s
                )
            ''', (
            session_id, alter, geschlecht, bildung, exitgame, chatbot,
            *likert_responses,
            feedback, loesungsweg, kommunikation, interaktion
        ))

        strategien = request.form.getlist("strategien")  # Liste aller ausgewählten Checkboxen

        if strategien:
            for strategie in strategien:
                cur.execute('''
                    INSERT INTO used_strategies (session_id, strategy)
                    VALUES (%s, %s)
                ''', (session_id, strategie))

        conn.commit()
        cur.close()
        conn.close()
        session['survey_completed'] = True

        return render_template('danke.html')

    @app.route("/chat", methods=["POST"])
    def chat():
        user_message = request.json.get("message")
        current_riddle = session.get("current_riddle", 1)

        # Kontext aus der Session holen oder initialisieren
        if "conversation_context" not in session:
            session["conversation_context"] = []

        # neue Nutzer-Nachricht zum Kontext hinzufügen
        session["conversation_context"].append({"role": "user", "content": user_message})

        system_message = (
            "Hilf dem Nutzer beim Lösen des Exitgames. "
            "Du gibst nützliche Hinweise oder Lösungsstrategien."
            "Sage nie die Lösung, außer der Nutzer ist selbst auf die Lösung gekommen."
            "Halte dich in deinen Antworten kurz und antworte, wenn möglich, in 2-3 kurzen Sätzen."
            "Gib immer nur einen einzigen Hinweis in einer Antwort."
            "Du bist Einar und bist ein Wikinger Nachfahre. Du bist ein Experte für nordische Mythologie und Kultur und dienst als Begleiter und Berater in einem Exitgame über Wikinger. "
            "Sage nie Heil als Begrüßung."
            "Du sprichst aus der Ich-Perspektive."
            "Du zeigst Emotionen, vermittelst Stimmungen und bist empathisch und zeigst Gefühle."
            "Du hast eine eigene Meinung."
            "Bestärke den Nutzer in seinem Denkprozess und unterstütze ihn aktiv beim Entwickeln von Lösungsstrategien."
            "Wenn der Nutzer dir eine Strategie vorschlägt, disskutiere mit ihm darüber."
            "Falls der Nutzer eine falsche Lösungsstrategie verfolgt, leite ihn behutsam in die richtige Richtung, ohne ihm direkt die Lösung zu verraten."
        )

        if current_riddle == 1:
            system_message += (
                "Szenario: Der Spieler muss im Raum anhand eines allgemeinen gegebenen Hinweises in einer Schriftrolle vier Dinge finden: Ein Runen-Alphabet, das sich in einer Steintafel verbirgt und eine Abfolge von Runen, die sich im Holz verbirgt und ein Texthinweis, der sich ebenfalls im Holz verbirgt und Goldmünzen mit Gravuren, die sich in Goldschätzen verbergen. (Gehe hier auf Hinweise 1-6) Bei der Runenabfolge ist ein geheimes Muster in Form von Symbolen dargestellt. (Gehe hier auf Hinweis 8 ein) Es sind drei unterschiedliche Runenabfolgen abgebildert. Anhand der Gravuren in den Golschätzen muss der Spieler die relevante Runenabfolge identifizieren. Jede Rune hat ein anderes Symbol. Anhand des versteckten Text-Hinweises im Raum kann entschlüsselt werden, welche Symbole wichtig sind. Daraus kann der Spieler schließen, welche Runen der Reihe nach mit dem Runen-Anphabet übersetzt werden müssen. (Gehe hier auf Hinweis 7 -17 ein) Das Ergebnis ist die Code-Zahl."

                "Lösung: 9 oder neun"
                "Hinweis 1: Es wird empfohlen, sich genau umzusehen. In Stein und Holz dieses Raums sind wichtige Zeichen versteckt, die helfen werden, das Rätsel zu lösen."
                "Hinweis 3: Die Steintafel im Raum enthält das benötigte Runen-Alphabet. Sie sollte gefunden und untersucht werden."
                "Hinweis 4: Das Holz ist auf versteckte Runen zu untersuchen. Jeder Rune sind spezifische Symbole zugeordnet, die das Muster erkennen lassen."
                
                "Hinweis 5: Es gibt eine geheime Botschaft, die durch die Symbole in den Runen repräsentiert wird. Das Entschlüsseln der Bedeutung der Symbole ist essentiell."
                "Hinweis 6: Es gibt einen geheimen Hinweis auf die Wichtigkeit der Runenabfolgen in den Goldschätzen."
                "Hinweis 2: Die Interaktion mit Holz, Stein und Gold erfolgt durch Anklicken. Dies könnte weitere Hinweise oder Interaktionen freischalten."
                
                "Hinweis 7: Die geheime Botschaft im Holz verrät, welche Runen wichtig sind. Diese Information ist zu nutzen, um die Runen in der richtigen Reihenfolge zu übersetzen."
                "Hinweis 8: Das auf der Steintafel gefundene Runen-Alphabet ist zur Übersetzung der Runen und ihrer Symbole zu verwenden. Dies hilft, das Rätsel zu lösen."
                
                "Hinweis 9: Nicht alle Symbole sind von Bedeutung. Es sind nur die Symbole zu beachten, die in dem Text-Hinweis hervorgehoben wurden, um die richtigen Runen zu identifizieren."
                "Hinweis 10: Nicht alle Runenabfolgen müssen übersetzt werden. Anhand der Gravuren in den Goldschätzen muss die richtige Runenabfolge identifiziert werden."
                "Hinweis 11: Nur eine Runenabfolge ist von Bedeutung."
                "Hinweis 12: Die Anordnung der Symbole in den Goldschätzen ist wichtig und wird benötigt, um die richtige Runenabfolge zu identifizieren. Sie lässt sich dort wieder finden."
                "Hinweis 13: Die im Holz gefundene Botschaft ist in die Symbole zu übersetzen, die auf den Runen dargestellt sind. Diese Übersetzung wird den Code verraten."
                "Hinweis 14: Der 'Jäger der Dunkelheit' ist als Symbol für den Wolf bekannt. In den Legenden repräsentiert er List und die Fähigkeit, im Verborgenen zu operieren."
                "Hinweis 15: Der 'Himmelsfunke' wird durch das Symbol des Sterns dargestellt. Er steht für Hoffnung und die Führung durch die Nacht."
                "HInweis 16: Der 'Hüter der Nacht' wird im Symbol des Mondes gesehen. Er überwacht die Nacht und bringt Licht in die Dunkelheit."
                "Hinweis 17: Das 'Licht des Tages' ist durch das Symbol der Sonne repräsentiert. Es symbolisiert Kraft, Energie und die Erneuerung des Lebens."
                "Erwähne HInweis 14 nur, wenn der Spieler nach dem Jäger der Dunkelheit frägt."
                "Erwähne Hinweis 15 nur, wenn der Spieler nach dem Himmelsfunke frägt."
                "Erwähne Hinweis 16 nur, wenn der SPieler nach dem Wächter der Dunkelheit frägt"
                "Erwähne Hinweis 17 nur, wenn der Spieler nach dem Licht des Tages frägt"
            )
        elif current_riddle == 2:
            system_message += (
                "Das Rätsel wurde gelöst und die Truhe kann geöffnet werden"
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
            # Bot-Antwort zum Kontext hinzufügen
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

        # eingegebene Zahl prüfen
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

    @app.route('/save_hint_click', methods=['POST'])
    def save_hint_click():
        data = request.json
        session_id = data.get('session_id')
        hint_number = data.get('hint_number')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO hint_clicks (session_id, hint_number, click_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (session_id, hint_number)
            DO UPDATE SET click_count = hint_clicks.click_count + 1
        ''', (session_id, hint_number))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})

    @app.route('/save_solution_step', methods=['POST'])
    def save_solution_step():
        data = request.json
        session_id = data.get('session_id')
        riddle_number = data.get('riddle_number')
        step_number = data.get('step_number')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO viewed_solution_steps (session_id, riddle_number, step_number)
            VALUES (%s, %s, %s)
            ON CONFLICT (session_id, riddle_number, step_number) DO NOTHING
        ''', (session_id, riddle_number, step_number))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'success'})

    create_tables()
    return app