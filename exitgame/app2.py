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


@app.route("/")
def index():
    session["chatbot_type"] = random.choice(["anthropomorph", "neutral"])
    session["code"] = ["_", "_", "_"]
    session["current_riddle"] = 1
    session["hints_used"] = 0
    return render_template("index.html")


@app.route("/game")
def game():
    return render_template("game2.html", chatbot_type=session["chatbot_type"])


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    chatbot_type = session.get("chatbot_type", "neutral")
    current_riddle = session.get("current_riddle", 1)

    system_message = (

            "Hilf dem Nutzer beim Lösen des Exitgames. "
            "Du gibst nützliche Hinweise."
            "Sage nie die Lösung. "
            "Halte dich in deinen Antworten kurz und antworte, wenn möglich, in 2-3 kurzen Sätzen."
            "Gib immer nur einen einzigen Hinweis in einer Antwort."
    )

    if chatbot_type == "anthropomorph":
        system_message += ("Du bist Einar und bist ein Wikinger Nachfahre. Du bist ein Experte für nordische Mythologie und Kultur und dienst als Begleiter und Berater in einem Exitgame über Wikinger. "
                           "Du sprichst aus der Ich-Perspektive."
                           "Du zeigst Emotionen, vermittelst Stimmungen und bist empathisch."
                           )

    else:
        system_message += ( "Du bist ein Experte der nordischen Mythologie. "
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
            "Der Spieler arbeitet an Rätsel 2: Die Schiffskarte."
            "Der Spieler erhält folgende Information: Die Pfade, die zwischen den Reichen der Götter schweben - von Asgard, der Heimat der Götter, über Jotunheim, das Land der Riesen, bis hinab nach Svartalfheim, dem Reich der Schatten - tragen das Echo uralter Geheimnisse."
            "Die Route führt von Asgard über Jotunheim nach Svartalfheim, die zweite Zahl des Codes."
            "Beispielhinweise: Schiffskarte finden, Schiffsroute"
            "Lösung: 2"
        )
    elif current_riddle == 3:
        system_message += (
            "Der Spieler arbeitet an Rätsel 3: Die Zeichen der Götter. "
            "Der Spierler erhält folgende Information: In den Schätzen ruht die Macht des Donners - ein Zeichen, das nur diejenigen erkennen, die das Auge des Weisen besitzen."
            "Ziel: Die Spieler müssen die Goldmünzen finden, wo die Zeichen der Götter abgebildet sind. Im Holz des Raumes finden sich diese wieder. Hier ist für jeden Gott eine Information hinterlegt. Die Spieler müssen das richtige Symbol für den Donnergott herausfinden, um die Zahl erhalten zu können."
            "Beipielhinweise: Donnergott, Goldschätze, Zeichen der Götter"
            "Lösung: 6"
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

    return jsonify({"response": chatbot_response, "current_riddle": session["current_riddle"]})


@app.route("/update_code", methods=["POST"])
def update_code():
    digit1 = request.json.get("digit1", "_")
    digit2 = request.json.get("digit2", "_")
    digit3 = request.json.get("digit3", "_")

    session["code"] = [digit1, digit2, digit3]

    # Fortschritt automatisch aktualisieren, sobald eine Eingabe erfolgt
    session["current_riddle"] = next((i + 1 for i, digit in enumerate(session["code"]) if digit == "_"), 4)

    # Nach Eingabe aller Zahlen prüfen, ob sie korrekt sind
    if all(digit != "_" for digit in session["code"]):
        if session["code"] == [str(correctCode[0]), str(correctCode[1]), str(correctCode[2])]:
            session["current_riddle"] = 4  # Alle Rätsel gelöst
        else:
            # Falls falsche Zahlen eingegeben wurden, nur falsche löschen
            for i in range(3):
                if session["code"][i] != str(correctCode[i]):
                    session["code"][i] = "_"
            session["current_riddle"] = next((i + 1 for i, digit in enumerate(session["code"]) if digit == "_"), 4)

    return jsonify({"code": session["code"], "current_riddle": session["current_riddle"]})

if __name__ == "__main__":
    app.run(debug=True)
