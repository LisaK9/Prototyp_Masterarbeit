from flask import Flask, render_template, request, jsonify, session
import openai
import random
import sqlite3
import time

# API-Schlüssel aus Datei laden
with open('api.key', 'r') as api_key_file:
    API_KEY = api_key_file.read().strip()

# OpenAI-Client initialisieren
openai_client = openai.OpenAI(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Der richtige Code
correctCode = [9, 2, 21]

@app.route("/")
def index():
    session_id = str(random.randint(100000, 999999))  # Einfache Session-ID
    session["session_id"] = session_id
    session["chatbot_type"] = random.choice(["anthropomorph", "neutral"])
    session["code"] = ["_", "_", "_"]
    session["current_riddle"] = 1
    session["hints_used"] = 0
    session["attempts"] = 0
    session["start_time"] = time.time()
    return render_template("start.html")


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

    system_message = (
        "Hilf dem Nutzer beim Lösen des Exitgames. "
        "Du gibst nützliche Hinweise oder Lösungsstrategien."
        "Sage nie die Lösung. "
        "Halte dich in deinen Antworten kurz und antworte, wenn möglich, in 2-3 kurzen Sätzen."
        "Gib immer nur einen einzigen Hinweis in einer Antwort."
    )

    if chatbot_type == "anthropomorph":
        system_message += ("Du bist Einar und bist ein Wikinger Nachfahre. Du bist ein Experte für nordische Mythologie und Kultur und dienst als Begleiter und Berater in einem Exitgame über Wikinger. "
                           "Du sprichst aus der Ich-Perspektive."
                           "Du zeigst Emotionen, vermittelst Stimmungen und bist empathisch."
                           "Du bestärkst den Nutzer beim finden von Lösungsstrategien."
                           "Wenn der Nutzer dir eine Strategie vorschlägt, disskutiere mit ihm darüber."
                           )

    else:
        system_message += ("Du bist ein Experte der nordischen Mythologie. "
                           "Du bist sachlich und neutral. "
                           "Du zeigst keine Emotionen, bist nicht empathisch und vermittelst keine Stimmungen. "
                           "Du bleibst immer sachlich und lieferst ausschließlich neutrale Fakten. "
                           "Erwähne bei dem Nutzer nie, dass du nur sachliche und neutrale Fakten lieferst. "
                           "Verwende keine Ich-Formulierungen."
                           )

    if current_riddle == 1:
        system_message += (
            " Der Spieler arbeitet an Rätsel 1."
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
            "Der Spieler erhält folgende Information: Wer die Welten Niflheim, Jotunheim, Svartalfheim, Asgard, Vanaheim und Midgard bereist, kann uralte Geheimnisse offenbaren."
            "Hinweis 1: Verweise auf die bereits vorhandene Information und erwähne, dass es sich hier um Teile von den 9 Welten handelt, die oft Als Baum assoziiert werden."
            "Hinweis 2: Erwähne, dass die richtige Reihenfolge der genannten Welten wichtig ist."
            "Hinweis 3: Erwähne, dass die Beschriftung der einzelnen Welten wichtig ist."
            "Hinweis 4: Es muss quasi eine Reiseroute gezeichnet werden, indem die Beschriftungen der erforderlichen Welten miteinander verbunden werden."
            "Hinweis 5: Die gezeichnete Reiseroute genauer betrachten. Eventuell verbirgt sich darin ja eine Zahl?"
            "Lösung: 2 oder zwei"
        )
    elif current_riddle == 3:
        system_message += (
            "Der Spieler arbeitet an Rätsel 3."
            "Der Spierler erhält folgende Information: In den Goldschätzen schlummert die Macht der Götter – wer Odins Pfad folgt, wird das Ziel erreichen."
            "Hinweis 1: Verweise auf die vorhande Information und darauf, dass nach Goldschätzen ausschau gehalten werden soll."
            "Hinweis 2: In den Golschätzen ist Odin, Thor und Loki abgebildet. Hier muss nach verborgenen Details ausschau gehalten werden."
            "Hinweis 3: Jeder Gott steht mit etwas bestimmten in Verbindung. Dies ist in den Goldmünzen zu erkennen. "
            "Hinweis 4: Die Zeichen der Götter finden sich im Raum wieder. "
            "Hinweis 5: In der gefunden Information über Odin sind versteckte Hinweise, die die letzte Zahl Bilden"
            "Hinweis 6: Ausschau halten nach bestimmten Wörtern, die mit einer Zahl in Verbindung stehen."
            "Erwähne nicht: Dass Odin der Allvater und Gott der Weisheit ist."
            "Erwähne nicht: Dass Odin mit zwei Raben in Beziehung steht."
            "Erwähne nicht: Dass Thor mit einem Hammer in Beziehung steht."
            "Erwähne nicht: Dass Thor der Donnergott und der Beschützer Midgards ist."
            "Erwähne nicht: Dass Loki mit zwei Hörnern in Beziehung steht."
            "Erwähne nicht: Dass Loki der Gott des Schabernacks und der Täuschung ist."
        
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
    digit = request.json.get("digit", "_")  # Die eingegebene Zahl
    riddle_number = request.json.get("riddle_number")  # Das aktuelle Rätsel (1, 2 oder 3)
    session_id = session.get("session_id")

    # **Überprüfe die eingegebene Zahl**
    if digit == str(correctCode[riddle_number - 1]):  # Wenn die Zahl korrekt ist
        session["current_riddle"] = riddle_number + 1  # Gehe zum nächsten Rätsel
        return jsonify({"status": "correct", "current_riddle": session["current_riddle"]})
    else:  # Wenn die Zahl falsch ist
        return jsonify({"status": "incorrect", "current_riddle": session["current_riddle"]})

if __name__ == "__main__":
    app.run(debug=True)