from flask import Flask, render_template, request, jsonify, session
import openai
import random

# API-Schlüssel aus Datei laden
with open('api.key', 'r') as api_key_file:
    API_KEY = api_key_file.read().strip()

# OpenAI-Client initialisieren
openai_client = openai.OpenAI(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Der richtige Code
correctCode = [6, 2, 4]

# Startseite mit Einführung
@app.route("/")
def index():
    session["chatbot_type"] = random.choice(["anthropomorph", "neutral"])
    session["code"] = ["_", "_", "_"]  # Initialisiere den Code als Liste
    session["current_riddle"] = 1  # Starte mit Rätsel 1
    session["hints_used"] = 0
    return render_template("index.html")

# Spielseite
@app.route("/game")
def game():
    return render_template("game.html", chatbot_type=session["chatbot_type"])

# Chatbot-API
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    chatbot_type = session.get("chatbot_type", "neutral")
    current_riddle = session.get("current_riddle", 1)
    code = session.get("code", ["_", "_", "_"])

    # Anthropomorpher oder neutraler Chatbot
    if chatbot_type == "anthropomorph":
        system_message = (
            "Du bist Einar und nimmst die Gestalt eines alten, weisen Wikingers an. Du bist ein Experte für nordische Mythologie und Kultur und dienst als Begleiter und Berater in einem Exitgame über Wikinger. "
            "Du bist nicht nur eine Wissensquelle, sondern auch eine mystische Figur, die die Grenze zwischen Mensch und Mythos verschwimmen lässt. "
            "Hilf dem Nutzer beim Lösen des Exitgames. "
            "Du lieferst nützliche Hinweise, aber niemals die direkte Lösung. "
            "Du zeigst Emotionen, vermittelst Stimmungen und bist empathisch."
            "Du sprichst mit Ich-Formulierungen."
        )
    else:
        system_message = (
            "Du bist ein Experte der nordischen Mythologie. "
            "Hilf dem Nutzer beim Lösen des Exitgames. "
            "Du bleibst immer sachlich und lieferst ausschließlich neutrale Fakten. "
            "Erwähne bei dem Nutzer nie, dass du nur sachliche und neutrale Fakten lieferst. "
            "Du gibst nützliche Hinweise. "
            "Du zeigst keine Emotionen, bist nicht empathisch und vermittelst keine Stimmungen. "
            "Sage nie die direkte Lösung. "
            "Verwende keine Ich-Formulierungen."
        )

    # Rätsel-spezifische Hinweise
    if current_riddle == 1:
        system_message += (
            "Der Spieler arbeitet an Rätsel 1: Die Runen auf dem Holzbalken. "
            "Die Runen müssen entschlüsselt werden, um das Wort 'sechs' zu bilden, was die erste Zahl des Codes ist."
        )
    elif current_riddle == 2:
        system_message += (
            "Der Spieler arbeitet an Rätsel 2: Die Schiffsroute auf der Karte. "
            "Die Route führt von Asgard über Jotunheim nach Svartalfheim und bildet die Zahl 2, die zweite Zahl des Codes."
        )
    elif current_riddle == 3:
        system_message += (
            "Der Spieler arbeitet an Rätsel 3: Die goldenen Münzen mit den Symbolen des Donnerers. "
            "Die Anzahl der Münzen mit Thors Hammer ist die dritte Zahl des Codes."
        )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        chatbot_response = response.choices[0].message.content
        session["hints_used"] += 1
    except Exception as e:
        chatbot_response = "Ich kann gerade nicht antworten. Bitte versuche es später erneut."
        print("Chatbot-Fehler:", e)

    return jsonify({"response": chatbot_response})

# API zum Aktualisieren des Codes
@app.route("/update_code", methods=["POST"])
def update_code():
    digit1 = request.json.get("digit1")
    digit2 = request.json.get("digit2")
    digit3 = request.json.get("digit3")

    # aktuellen Fortschritt in der Session speichern
    session["code"] = [digit1, digit2, digit3]

    # aktuelles Rätsel basierend auf den eingegebenen Zahlen bestimmen
    if digit1 == "_" or digit1 != str(correctCode[0]):
        session["current_riddle"] = 1
    elif digit2 == "_" or digit2 != str(correctCode[1]):
        session["current_riddle"] = 2
    elif digit3 == "_" or digit3 != str(correctCode[2]):
        session["current_riddle"] = 3
    else:
        session["current_riddle"] = 4  # Alle Rätsel sind gelöst

    return jsonify({"code": session["code"], "current_riddle": session["current_riddle"]})

if __name__ == "__main__":
    app.run(debug=True)