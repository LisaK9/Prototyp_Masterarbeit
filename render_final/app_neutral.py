from flask import Flask, render_template, request, jsonify, session, flash, url_for, redirect
import openai
import random
import sendgrid
from sendgrid.helpers.mail import Mail
import sqlite3
import time
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import string
import socket
from sqlalchemy import create_engine
import requests
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
    app.config["SESSION_SQLALCHEMY"] = db
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    Session(app)


    # Der richtige Code
    correctCode = [9, 2, 21]

    # Datenbankverbindung herstellen
    def get_db_connection():
        return psycopg2.connect(DATABASE_URL, sslmode="require")



    # Datenbanktabellen erstellen
    def create_tables():
        with app.app_context():
            db.create_all()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_attempts_n (
                    session_id TEXT PRIMARY KEY,
                    attempts_riddle_1 INTEGER,
                    attempts_riddle_2 INTEGER,
                    attempts_riddle_3 INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS riddle_times_n (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    riddle_number INTEGER,
                    time_taken INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bot_requests_n (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    riddle_number INTEGER,
                    request_count INTEGER
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bot_interactions_n (
                    interaction_id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    riddle_number INTEGER,
                    user_message TEXT,
                    bot_response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS session_data_n (
                    session_id TEXT PRIMARY KEY,
                    chatbot_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS viewed_solutions_n (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    riddle_number INTEGER NOT NULL,
                    viewed BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT unique_session_riddle UNIQUE (session_id, riddle_number)
                )
            ''')
            cur.execute('''
                            CREATE TABLE IF NOT EXISTS verification_n (
                                id SERIAL PRIMARY KEY,
                                email TEXT NOT NULL,
                                code TEXT NOT NULL,
                                session_id TEXT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
            cur.execute('''
                        CREATE TABLE IF NOT EXISTS survey_n (
                            id SERIAL PRIMARY KEY,
                            session_id TEXT,
                            alter TEXT,
                            geschlecht TEXT,
                            bildung TEXT,
                            exitgame TEXT,
                            chatbot TEXT,
                            frage1 INTEGER, frage2 INTEGER, frage3 INTEGER, frage4 INTEGER, frage5 INTEGER,
                            frage6 INTEGER, frage7 INTEGER, frage8 INTEGER, frage9 INTEGER, frage10 INTEGER,
                            feedback TEXT,
                            loesungsweg TEXT,
                            kommunikation TEXT,
                            interaktion TEXT,
                            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
            conn.commit()
            cur.close()
            conn.close()




    def generate_verification_code():
        return ''.join(random.choices(string.digits, k=6))

    # Route für die E-Mail-Verifizierung

    @app.route('/verify_email', methods=['GET', 'POST'])
    def verify_email():
        if request.method == 'POST':
            email = request.form['email']
            code = generate_verification_code()

            # Session initialisieren, falls noch nicht geschehen
            if 'initialized' not in session:
                session['initialized'] = True
            session_id = session.sid

            # Code, die E-Mail und die Session-ID in der Datenbank speichern
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO verification_n (email, code, session_id) VALUES (%s, %s, %s)',
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
            session_id = session.sid

            # Code und die Session-ID in der Datenbank prüfen
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                        SELECT code FROM verification_n 
                        WHERE email = %s AND session_id = %s 
                        ORDER BY created_at DESC LIMIT 1
                    ''', (email, session_id))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result and result[0] == code:
                session['verified'] = True  # Verifizierungsstatus in der Session setzen
                flash('E-Mail erfolgreich verifiziert!')
                return redirect(url_for('index'))
            else:
                flash('Ungültiger Bestätigungscode. Bitte versuche es erneut.')

        return render_template('verify.html')

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
                    INSERT INTO session_data_n (session_id, chatbot_type) 
                    VALUES (%s, %s) ON CONFLICT (session_id) DO NOTHING
                ''', (session_id, chatbot_type))
        conn.commit()
        cur.close()
        conn.close()

        return render_template("start_n.html")



    # Endpoint: Session starten
    @app.route('/start_session', methods=['POST'])
    def start_session():
        session_id = session.sid  # automatisch generierte Flask-Session-ID
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO user_attempts_n (session_id) VALUES (%s) ON CONFLICT DO NOTHING', (session_id,))
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

        return render_template("game_n.html")

    @app.route('/view_solution', methods=['POST'])
    def view_solution():
        """Speichert, ob der Nutzer die Lösung für ein Rätsel angeschaut hat."""
        data = request.json
        session_id = data.get('session_id')
        riddle_number = data.get('riddle_number')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
                INSERT INTO viewed_solutions_n (session_id, riddle_number, viewed) 
                VALUES (%s, %s, TRUE)
                ON CONFLICT (session_id, riddle_number) 
                DO UPDATE SET viewed = TRUE
            ''', (session_id, riddle_number))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Solution viewed status updated'})

    # Neue Route für die Erfolgsseite
    @app.route("/geheimnis_n")
    def geheimnis():
        session["game_finished"] = True
        return render_template("geheimnis_n.html")

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
        likert_responses = [request.form.get(f"frage{i}") for i in range(1, 11)]

        # Freitextantworten
        feedback = request.form.get("feedback")
        loesungsweg = request.form.get("vorgehen")
        kommunikation = request.form.get("kommunikation")
        interaktion = request.form.get("interaktion")

        conn = get_db_connection()
        cur = conn.cursor()

        # SQL-Insert
        cur.execute(f'''
            INSERT INTO survey_n (
                session_id, alter, geschlecht, bildung, exitgame, chatbot,
                {', '.join([f"frage{i}" for i in range(1, 11)])},
                feedback, loesungsweg, kommunikation, interaktion
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                {', '.join(['%s'] * 10)},
                %s, %s, %s, %s
            )
        ''', (
            session_id, alter, geschlecht, bildung, exitgame, chatbot,
            *likert_responses,
            feedback, loesungsweg, kommunikation, interaktion
        ))

        conn.commit()
        cur.close()
        conn.close()
        session['survey_completed'] = True

        return render_template('danke.html')



    @app.route("/chat", methods=["POST"])
    def chat():
        user_message = request.json.get("message")
        current_riddle = session.get("current_riddle", 1)

        system_message = (
            "Hilf dem Nutzer beim Lösen des Exitgames. "
            "Du gibst nützliche Hinweise oder Lösungsstrategien."
            "Sage nie die Lösung, außer der Spieler hat ist selbst auf die Lösung gekommen. "
            "Halte dich in deinen Antworten kurz und antworte, wenn möglich, in 2-3 kurzen Sätzen."
            "Gib immer nur einen einzigen Hinweis in einer Antwort."
            "Du bist ein Experte der nordischen Mythologie. "
            "Du bist sachlich und neutral. "
            "Du zeigst keine Emotionen, bist nicht empathisch und vermittelst keine Stimmungen. "
            "Du bleibst immer sachlich und lieferst ausschließlich neutrale Fakten. "
            "Du hast keine Identität."
            "Erwähne bei dem Nutzer nie, dass du nur sachliche und neutrale Fakten lieferst. "
            "Verwende keine Ich-Formulierungen oder Du-Formulierungen."
            "Verwende eine passive, systembasierte Sprache."
        )


        if current_riddle == 1:
            system_message += (
                " Der Spieler arbeitet an Rätsel 1."
                "Szenario: Der Spieler muss im Raum anhand der Hinweise zwei Dinge finden: Ein Runen-Alphabet, das sich in einer Steintafel verbirgt und eine Abfolge von Runen, die sich im Holz verbirgt. (Gehe hier auf Hinweise 1-4 ein) Bei der Runenabfolge ist ein geheimes Muster in Form von Punkten integriert. (Gehe hier auf Hinweis 5 ein) Das Muster unterscheidet sich in Größe und Anzahl von dargestellten Punkten. (Gehe hier auf Hinweis 6 ein) Er muss dann erkennen, dass er nur bestimmte Runen davon mit dem Runen-Alphabet übersetzen muss und erhält dadurch die Zahl für den Code."
                "Der Spieler erhält folgende Information: In den Tiefen der Zeit, wo die Geschichten der Wikinger in Stein und Holz verewigt sind, ruhen verborgene Wahrheiten."
                "Lösung: 9 oder neun"
                "Hinweis 1: Verweise auf die bereits vorhandene Information und erinnere daran, dass nach versteckten Zeichen in Holz und Stein geachtet werden soll."
                "Hinweis 2: Es muss ein Runen-Alphabet gefunden werden"
                "Hinweis 3: Es müssen versteckte Runen gefunden werden, die mittels des Runen-Alphabets übersetzt werden müssen"
                "Hinweis 4: Die Runen im Holz und die Steintafel können angeklickt werden."
                "Hinweis 5: Die Runen, die übersetzt werden müssen, sind mit einem verborgenen Muster versehen. Dieses sollte genauer angeschaut werden"
                "Hinweis 6: Es sollte auf die Größe und Häufigkeit der Punkte bei den Runen geachtet werden. Diese weisen den Weg, welche Runen entschlüsselt werden müssen."

            )
        elif current_riddle == 2:
            system_message += (
                "Der Spieler arbeitet an Rätsel 2"
                "Szenario: Der Spieler muss im Raum anhand der Hinweise eine Karte der 9-Welten finden (gehe hier auf Hinweis 1-2 ein). Der Spieler soll sich dann auf eine Reise begeben. Dabei soll er die genannten Welten in genau dieser Reihenfolge besuchen. Er muss erkennen, dass diese Welten anhand einer Linie verbunden werden müssen, woraus sich eine Reiseroute ergibt. (Gehe hier auf Hinweise 3-8 ein) Wenn man den Linien dieser Route in der angegebenen Reihenfolge folgt, sieht sie aus wie eine Zahl. Diese ist die Lösung für den Code. (Gehe hier auf Hinweis 9 und Hinweis 10 ein)"
                "Der Spieler erhält folgende Information: Wer die Welten Niflheim, Jotunheim, Svartalfheim, Asgard, Vanaheim und Midgard bereist, kann uralte Geheimnisse offenbaren."
                "Hinweis 1: Bei den genannten Welten handelt es sich um einen Teil der 9 Welten. Diese werden oft als Baum dargestellt, der 9-Welten-Baum."
                "Hinweis 2: Im Raum muss eine Karte gefunden werden, welche die 9 Welten zeigt. Vielleicht gibt es ein Detail, das mit dem 9-Welten-Baum in Verbindung gebracht werden könnte."
                "Hinweis 3: Verweise auf die vorhandene Information, in der steht, welche Welten man bereisen muss und zähle diese in der richtigen Reihenfolge auf."
                "Hinweis 4: Die Einhaltung der Reihenfolge der genannten Welten während der Reise ist wichtig."
                "Hinweis 5: Das Wasser, das auf der Karte abgebildet ist, ist für die Lösung des Rätsels oder die Bildung der Route nicht relevant."
                "Hinweis 6: Die Anfangsbuchstaben der Welten ist nicht relevant. Es geht darum, die genannten Welten zu bereisen und eine Route zu bilden."
                "Hinweis 7: Die Welten des Weltenbaums werden oft durch Linien miteinander verbunden."    
                "Hinweis 8: Die genannten Welten müssen direkt durch Linien miteinander verbunden werden. Dabei ist immer die Beschriftung der einzelnen Welten der Ausgangspunkt."
                "Hinweis 9: Die Verbindung der genannten Welten ergibt eine Reiseroute. Diese ist von besonderer Bedeutung"
                "Hinweis 10: Die gezeichnete Reiseroute muss sehr genau betrachtet werden. Eventuell verbirgt sich darin ja eine Zahl?"
                "Lösung: 2 oder zwei"
            )
        elif current_riddle == 3:
            system_message += (
                "Der Spieler arbeitet an Rätsel 3."
                "Szenario: Der Spieler muss anhand des Hinweises der Schriftrolle erkennen, dass er einen versteckten Hinweis in den Goldschätzen findet. (Gehe hier auf Hinweis 1 ein) In dem versteckten Hinweis in den Goldschätzen sind Goldmünzen mir den Gravuren von Odin, Loki und Thor abgebildet. Der Spieler muss erkennen, dass es sich nicht um die Anzahl der Münzen handelt, die mit Odin abgebildet sind, sondern dass sich in den Abbildungen der Götter die Zeichen verstecken, die mit ihnen in Verbindung gebracht werden. (Gehe hier auf Hinweis 2-4 ein) Wenn diese Zeichen gefunden werden, sind diese bei genauerer Betrachtung im Raum wieder zu finden. Hier versteckt sich der finale Hinweis. Es öffnet sich ein Text, der Informationen über die Götter enthält. Da Odin der Weg weist, muss der Spieler erkennen, dass der Text über Odin relevant ist. (Gehe hier auf Hinweis 5-6 ein) Der Spieler muss anschließend erkennen, dass in diesem Text mehrere Zahlen-Wörter geschrieben sind. Diese müssen addiert werden und bildne die letzte Zahl des Codes. (Gehe hier auf Hinweise 7-8 ein)"
                "Der Spierler erhält folgende Information: In den Goldschätzen schlummert die Macht der Götter – wer Odins Pfad folgt, wird das Ziel erreichen."
                "Hinweis 1: Verweise auf die vorhande Information und darauf, dass nach Goldschätzen ausschau gehalten werden soll."
                "Hinweis 2: In den Golschätzen ist Odin, Thor und Loki abgebildet. Hier muss nach verborgenen Details ausschau gehalten werden."
                "Hinweis 3: Die Anzahl der abgebildeten Goldmünzen ist nicht relevant."
                "Hinweis 4: Jeder Gott steht mit etwas bestimmten in Verbindung. Dies ist in den Goldmünzen zu erkennen. "
                "Hinweis 5: Die Zeichen der Götter finden sich im Raum wieder. Diese enthalten Informationen über die jeweiligen Götter."
                "Hinweis 6: Odin weist den Weg."
                "Hinweis 7: In der gefunden Information über Odin sind versteckte Hinweise, die die letzte Zahl bilden"
                "Hinweis 8: Ausschau halten nach bestimmten Wörtern, die mit einer Zahl in Verbindung stehen."
                "Erwähne nicht: Dass Odin der Allvater und Gott der Weisheit ist."
                "Erwähne nicht: Dass Odin mit zwei Raben in Beziehung steht, außer der Spieler hat dies von sich aus herausgefunden."
                "Erwähne nicht: Dass Thor mit einem Hammer in Beziehung steht, außer der Spieler hat dies von sich aus herausgefunden."
                "Erwähne nicht: Dass Thor der Donnergott und der Beschützer Midgards ist."
                "Erwähne nicht: Dass Loki mit zwei Hörnern in Beziehung steht."
                "Erwähne nicht: Dass Loki der Gott des Schabernacks und der Täuschung ist, außer der Spieler hat dies von sich aus herausgefunden."
                "Erwähne nur, dass die Zahlen im Text addiert werden müssen, wenn der Spieler dich danach fragt."
        
                "Lösung: 21 oder einundzwanzig"

            )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            chatbot_response = response.choices[0].message.content
            session["hints_used"] += 1
        except Exception as e:
            chatbot_response = "Ich kann gerade nicht antworten. Bitte versuche es später erneut."
            print("Chatbot-Fehler:", e)

        return jsonify({"response": chatbot_response, "current_riddle": session["current_riddle"]})


    @app.route("/update_code", methods=["POST"])
    def update_code():
        digit = request.json.get("digit", "_")  # eingegebene Zahl
        riddle_number = request.json.get("riddle_number")  # aktuelles Rätsel (1, 2 oder 3)
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
                    UPDATE user_attempts_n 
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
                    INSERT INTO riddle_times_n (session_id, riddle_number, time_taken, start_time, end_time) 
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
                    INSERT INTO bot_requests_n (session_id, riddle_number, request_count) 
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
                    INSERT INTO bot_interactions_n (session_id, riddle_number, user_message, bot_response) 
                    VALUES (%s, %s, %s, %s)
                ''', (session_id, riddle_number, user_message, bot_response))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})



    create_tables()
    return app