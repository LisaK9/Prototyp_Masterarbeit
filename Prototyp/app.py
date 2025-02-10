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
correctCode = [9, 2, 6]

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
            " Der Spieler arbeitet an Rätsel 1: Die Runen. "
            "Der Spieler erhält folgende Information: In den tiefen der Zeit, wo die Geschichten der Wikinger in Stein, Holz und Gold verewigt sind, liegt der Schlüssel verborgen. Die Runen, alt wie die Welten selbst, flüstern von vergessenen Wahrheiten."
            "Ziel: Die Runen müssen entschlüsselt werden, was die erste Zahl des Codes ist."
            "Lösung: 9 oder neun"
            "Beispielhinweise: Runen-Alphabet, Runen-Entschlüsselung, Runen finden, die entschlüsselt werden sollen, Hinweis beachten, dass Wikinger in Stein, Gold und Holz verewigen"
            "Wenn der Spieler die Runen, die übersetzt werden müssen gefunden hat, aber nicht weiß, welche er übersetzen soll, gib einen Hinweis auf Punkte."
        )
    elif current_riddle == 2:
        system_message += (
            "Der Spieler arbeitet an Rätsel 2: Die Schiffskarte der neun Welten."
            "Der Spieler erhält folgende Information: Die Pfade, die zwischen den Reichen der Götter schweben - von Asgard, der Heimat der Götter, über Jotunheim, das Land der Riesen, bis hinab nach Svartalfheim, dem Reich der Schatten - tragen das Echo uralter Geheimnisse."
            "Die Route führt von Asgard über Jotunheim nach Svartalfheim, die zweite Zahl des Codes."
            "Beispielhinweise: 9-Welten Baum, Schiffskarte finden, Schiffsroute"
            "Lösung: 2 oder zwei"
        )
    elif current_riddle == 3:
        system_message += (
            "Der Spieler arbeitet an Rätsel 3: Die Zeichen der Götter. "
            "Der Spierler erhält folgende Information: In den Schätzen ruht die Macht des Donners - ein Zeichen, das nur diejenigen erkennen, die das Auge des Weisen besitzen."
            "Ziel: Die Spieler müssen die Goldmünzen finden, wo die Zeichen der Götter abgebildet sind. Im Raum findet finden sich die Zeichen der Götter wieder. Hier ist für jeden Gott eine Information hinterlegt. Die Spieler müssen das richtige Symbol für den Donnergott herausfinden, um die Zahl erhalten zu können."
            "Beipielhinweise: auf vorliegende Information hinweisen, Goldschätze, Donnergott, Zeichen der Götter im Raum"
            "Lösung: 6 oder sechs"
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