const correctCode = [9, 2, 21]; // Der richtige Code: 6-2-4

let currentRiddle = 1;  // Speichert das zuletzt aktive Rätsel

// Aktiviere das erste Eingabefeld beim Laden der Seite
document.getElementById('code-digit-1').disabled = false;
document.getElementById('code-digit-1').focus();

// Funktion zum Aktualisieren der Klickbarkeit der Hinweise
function updateHintAreas(currentRiddle) {
    // Deaktiviere alle Hinweisflächen zunächst
    document.querySelectorAll('.hint-area').forEach(hintArea => {
        hintArea.style.pointerEvents = 'none'; // Deaktiviere Klicks
    });

    // Aktiviere die Hinweisflächen basierend auf dem aktuellen Rätsel
    if (currentRiddle === 1) {
        // Aktiviere Hinweis 1 und 2 für Rätsel 1
        document.getElementById('hint1-area').style.pointerEvents = 'auto';
        document.getElementById('hint2-area').style.pointerEvents = 'auto';
    } else if (currentRiddle === 2) {
        // Aktiviere Hinweis 3 für Rätsel 2
        document.getElementById('hint3-area').style.pointerEvents = 'auto';
    } else if (currentRiddle ===3){
    // Für Rätsel 3 werden keine Hinweise aktiviert
        document.getElementById('hint4-area').style.pointerEvents = 'auto';
        document.getElementById('hint5-area').style.pointerEvents = 'auto';
        document.getElementById('hint6-area').style.pointerEvents = 'auto';
        document.getElementById('hint7-area').style.pointerEvents = 'auto';
        document.getElementById('hint8-area').style.pointerEvents = 'auto';
        document.getElementById('hint9-area').style.pointerEvents = 'auto';
    }
}

// Beim Laden der Seite die Klickbarkeit der Hinweise initialisieren
document.addEventListener('DOMContentLoaded', function() {
    updateHintAreas(currentRiddle);
});

let sessionId;  // Globale Variable für die Session-ID

// Initialisiere ein Objekt, um die Anzahl der Versuche für jedes Rätsel zu speichern
const attemptsTracker = {
    1: 0, // Versuche für Rätsel 1
    2: 0, // Versuche für Rätsel 2
    3: 0  // Versuche für Rätsel 3
};

const startTimes = {
    1: null, // Startzeit für Rätsel 1
    2: null, // Startzeit für Rätsel 2
    3: null  // Startzeit für Rätsel 3
};

const botRequestCounts = {
    1: 0, // Bot-Anfragen für Rätsel 1
    2: 0, // Bot-Anfragen für Rätsel 2
    3: 0  // Bot-Anfragen für Rätsel 3
};

// Funktion zum Starten einer neuen Session
function startSession() {
    fetch('/start_session', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        sessionId = data.session_id;  // Speichere die Session-ID
        console.log('Session gestartet:', sessionId);
    })
    .catch(error => console.error('Fehler beim Starten der Session:', error));
}

// Funktion zum Speichern der Interaktion
function saveInteractionToDatabase(riddleNumber, userMessage, botResponse) {
    fetch('/save_interaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            riddle_number: riddleNumber,
            user_message: userMessage,
            bot_response: botResponse
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Interaktion gespeichert:', data);
    })
    .catch(error => console.error('Fehler beim Speichern der Interaktion:', error));
}

// Funktion zum Speichern der Versuche in der Datenbank
function saveAttemptsToDatabase() {
    fetch('/save_attempts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            attempts_riddle_1: attemptsTracker[1],
            attempts_riddle_2: attemptsTracker[2],
            attempts_riddle_3: attemptsTracker[3]
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Versuche gespeichert:', data);
    })
    .catch(error => console.error('Fehler beim Speichern der Versuche:', error));
}

// Funktion zum Speichern der Zeit für ein Rätsel
function saveTimeToDatabase(riddleNumber, timeTaken, startTime, endTime) {
    fetch('/save_time', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            riddle_number: riddleNumber,
            time_taken: timeTaken,
            start_time: startTime.toISOString(),  // Startzeit als ISO-String
            end_time: endTime.toISOString()     // Endzeit als ISO-String
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Zeit gespeichert:', data);
    })
    .catch(error => console.error('Fehler beim Speichern der Zeit:', error));
}

// Funktion zum Speichern der Bot-Anfragen
function saveBotRequestsToDatabase(riddleNumber, requestCount) {
    fetch('/save_bot_request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            riddle_number: riddleNumber,
            request_count: requestCount
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Bot-Anfragen gespeichert:', data);
    })
    .catch(error => console.error('Fehler beim Speichern der Bot-Anfragen:', error));
}

// Funktion, um die Truhe klickbar zu machen
function makeChestClickable() {
    const chestImage = document.querySelector('.chest-image');
    if (chestImage) {
        chestImage.style.cursor = 'pointer'; // Zeige einen Zeiger an, um anzuzeigen, dass die Truhe klickbar ist
        chestImage.addEventListener('click', function() {
            // Überprüfe, ob der gesamte Code korrekt eingegeben wurde
            if (currentRiddle === 3 && attemptsTracker[3] > 0) {
                // Öffne eine neue HTML-Seite
                window.location.href = '/geheimnis'; // Ändere '/neue_seite.html' zu deiner gewünschten Seite
            }
        });
    }
}

function checkDigit() {
    const input = document.getElementById(`code-digit-${currentRiddle}`);
    const feedback = document.getElementById('code-feedback');
    const enteredDigit = input.value.trim();

    // Prüfen, ob die Eingabe eine Zahl ist
    if (enteredDigit && isNaN(enteredDigit)) {
        feedback.textContent = `Bitte eine gültige Zahl (0-9) eingeben.`;
        feedback.style.color = 'red';
        input.value = '';
        return;
    }

    // Startzeit für das Rätsel setzen, falls noch nicht geschehen
    if (!startTimes[currentRiddle]) {
        startTimes[currentRiddle] = new Date();  // Aktuelle Zeit als Date-Objekt
    }
    // Erhöhe den Versuchszähler für das aktuelle Rätsel
    attemptsTracker[currentRiddle]++;

    // Sende die eingegebene Zahl zur Überprüfung
    fetch('/update_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ digit: enteredDigit, riddle_number: currentRiddle })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "correct") {
            feedback.textContent = "Richtig!";
            feedback.style.color = 'green';

            // Berechne die benötigte Zeit für das Rätsel
            const endTime = new Date();  // Aktuelle Zeit als Date-Objekt
            const timeTaken = Math.floor((endTime - startTimes[currentRiddle]) / 1000); // Zeit in Sekunden

            // Speichere die Zeit in der Datenbank
            saveTimeToDatabase(currentRiddle, timeTaken, startTimes[currentRiddle], endTime);

            // Speichere die Bot-Anfragen in der Datenbank
            saveBotRequestsToDatabase(currentRiddle, botRequestCounts[currentRiddle]);

            // Sende eine Nachricht an den Chatbot, um Feedback zu geben
            sendChatbotFeedback(currentRiddle);

            // Aktiviere das nächste Eingabefeld
            if (currentRiddle < 3) {
                currentRiddle = data.current_riddle; // Aktualisiere den Rätselstatus
                document.getElementById(`code-digit-${currentRiddle}`).disabled = false;
                document.getElementById(`code-digit-${currentRiddle}`).focus();
                // Aktualisiere die Klickbarkeit der Hinweise für das neue Rätsel
                updateHintAreas(currentRiddle);
            } else {
                feedback.textContent = "Code erfolgreich eingegeben!";
                // Speichere die Versuche in der Datenbank
                saveAttemptsToDatabase();
                makeChestClickable();
            }
        } else {
            feedback.textContent = "Falsch! Versuche es erneut.";
            feedback.style.color = 'red';
            input.value = ''; // Leere das Feld
            input.focus(); // Setze den Fokus zurück
            // Sende ein zufälliges Feedback vom Chatbot für eine falsche Antwort
            sendChatbotWrongAnswerFeedback();
        }
    })
    .catch(error => console.error('Error bei /update_code:', error));
}

// Starte eine neue Session, wenn das Spiel geladen wird
document.addEventListener('DOMContentLoaded', function() {
    startSession();
    updateHintAreas(currentRiddle);
});

// Event-Listener für die Eingabefelder, um die Entertaste zu unterstützen
document.querySelectorAll('#code-input input').forEach(input => {
    input.addEventListener('keydown', function(event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Verhindere das Standardverhalten der Entertaste
            checkDigit(); // Überprüfe die eingegebene Zahl
        }
    });
});

// Funktion, um Feedback vom Chatbot anzuzeigen, wenn ein Rätsel gelöst wurde
function sendChatbotFeedback(riddleNumber) {
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');

    // Definiere die Feedback-Nachrichten für jedes Rätsel
    const feedbackMessages = {
        1: "Hah! Du hast die Zeichen der Ahnen verstanden! Diese Runen sind älter als meine Großmutter – und glaub mir, sie war alt wie die Berge! Nur die Klugen und Weisen erkennen das verborgene Muster. Ich spüre, dass du den Geist eines echten Skalden in dir trägst! Doch noch ist dein Weg nicht beendet. Dein nächster Schritt führt dich auf eine Reise durch die Welten. Mach dich bereit – keine Fahrt verläuft ohne Sturm!",
        2: "Fantastisch, du hast den verborgenen Pfad gesehen! So wie einst meine Vorfahren die Meere mit ihren Drachenbooten durchquerten, hast du die richtige Route gefunden. Ich erinnere mich an die Geschichten am Feuer – von Kriegern, die den Weg durch die Welten kannten. Du hast ihre Spur erkannt! Doch sei auf der Hut... Die größten Geheimnisse sind nicht in Stein gemeißelt, sondern verbergen sich oft im Glanz des Goldes. Und Gold kann trügen!",
        3: "Bei Mjölnirs Zorn! Du hast es geschafft! Odin selbst würde dir auf die Schulter klopfen – und glaub mir, das ist eine Ehre, die nicht vielen zuteilwird! Du hast die Zeichen gesehen, die Hinweise entschlüsselt und den Weg der Götter verstanden. Das Blut der Nordmänner fließt durch deine Adern, das spüre ich! Öffne nun die Truhe und entdecke, was in ihrem Inneren auf dich wartet."
    };

    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    // Simuliere eine kurze Verzögerung, bevor die Nachricht angezeigt wird
    setTimeout(() => {
        // Ladeanimation ausblenden
        loadingDots.style.display = 'none';

        // Füge die Feedback-Nachricht des Chatbots zum Chatfenster hinzu
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${feedbackMessages[riddleNumber]}</p>`;
        chatWindow.appendChild(botMessageElement);

        // Scrollen Sie zum Ende des Chatfensters
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 1000); // 1 Sekunde Verzögerung
}

// Funktion, um Feedback vom Chatbot anzuzeigen, wenn ein Rätsel gelöst wurde
function sendChatbotFeedback(riddleNumber) {
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');

    // Definiere die Feedback-Nachrichten für jedes Rätsel
    const feedbackMessages = {
        1: "Hah! Du hast die Zeichen der Ahnen verstanden! Diese Runen sind älter als meine Großmutter – und glaub mir, sie war alt wie die Berge! Nur die Klugen und Weisen erkennen das verborgene Muster. Ich spüre, dass du den Geist eines echten Skalden in dir trägst! Doch noch ist dein Weg nicht beendet. Dein nächster Schritt führt dich auf eine Reise durch die Welten. Mach dich bereit – keine Fahrt verläuft ohne Sturm!“",
        2: "Fantastisch! Du hast den verborgenen Pfad gesehen! So wie einst meine Vorfahren die Meere mit ihren Drachenbooten durchquerten, hast du die richtige Route gefunden. Ich erinnere mich an die Geschichten am Feuer – von Kriegern, die den Weg durch die Welten kannten. Du hast ihre Spur erkannt! Doch sei auf der Hut... Die größten Geheimnisse sind nicht in Stein gemeißelt, sondern verbergen sich oft im Glanz des Goldes. Und Gold kann trügen!",
        3: "Bei Mjölnirs Zorn! Du hast es geschafft! Odin selbst würde dir auf die Schulter klopfen – und glaub mir, das ist eine Ehre, die nicht vielen zuteilwird! Du hast die Zeichen gesehen, die Hinweise entschlüsselt und den Weg der Götter verstanden. Das Blut der Nordmänner fließt durch deine Adern, das spüre ich! Doch sei gewarnt – mit Wissen kommt Verantwortung. Die Wahrheit, die du gleich erfahren wirst, ist mächtig. Stelle dich ihr mit Ehre und Mut und öffne die Truhe!"
    };

    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    // Simuliere eine kurze Verzögerung, bevor die Nachricht angezeigt wird
    setTimeout(() => {
        // Ladeanimation ausblenden
        loadingDots.style.display = 'none';

        // Füge die Feedback-Nachricht des Chatbots zum Chatfenster hinzu
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${feedbackMessages[riddleNumber]}</p>`;
        chatWindow.appendChild(botMessageElement);

        // Scrollen Sie zum Ende des Chatfensters
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 1000); // 1 Sekunde Verzögerung
}

// Funktion, um zufälliges Feedback für eine falsche Antwort zu geben
function sendChatbotWrongAnswerFeedback() {
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');

    // Liste von möglichen Feedback-Nachrichten für falsche Antworten
    const wrongAnswerMessages = [
        "Hmm, das war nicht richtig. Versuche es noch einmal!",
        "Nicht ganz, aber gib nicht auf! Die Wikinger waren auch hartnäckig.",
        "Falsch geraten! Vielleicht hilft dir ein Hinweis weiter.",
        "Das war leider nicht die richtige Zahl. Probiere es nochmal!",
        "Nicht korrekt, aber du bist auf dem richtigen Weg!",
        "Die Götter sind heute nicht auf deiner Seite. Versuche es erneut!",
        "Falsch! Aber keine Sorge, jeder Fehler bringt dich der Lösung näher."
    ];

    // Wähle eine zufällige Nachricht aus der Liste aus
    const randomMessage = wrongAnswerMessages[Math.floor(Math.random() * wrongAnswerMessages.length)];

    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    // Simuliere eine kurze Verzögerung, bevor die Nachricht angezeigt wird
    setTimeout(() => {
        // Ladeanimation ausblenden
        loadingDots.style.display = 'none';

        // Füge die zufällige Feedback-Nachricht des Chatbots zum Chatfenster hinzu
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${randomMessage}</p>`;
        chatWindow.appendChild(botMessageElement);

        // Scrollen Sie zum Ende des Chatfensters
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 1000); // 1 Sekunde Verzögerung
}

// **Event-Listener für den Checken-Button**
document.getElementById('check-button').addEventListener('click', checkDigit);


document.getElementById('chat-input').addEventListener('keydown', function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});
function toggleChat() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.classList.toggle('active');
}

// **Funktion zum Senden einer Nachricht an den Chatbot**
function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');
    const userMessage = chatInput.value.trim();

    if (!userMessage) return;  // Keine Nachricht senden, wenn das Eingabefeld leer ist

    // Erhöhe den Zähler für Bot-Anfragen
    botRequestCounts[currentRiddle]++;

    // Benutzernachricht im Chatfenster anzeigen
    const userMessageElement = document.createElement('div');
    userMessageElement.classList.add('message', 'user');
    userMessageElement.innerHTML = `<p>${userMessage}</p>`;
    chatWindow.appendChild(userMessageElement);

    chatInput.value = '';  // Eingabefeld leeren
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    // Nachricht an den Chatbot senden
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Ladeanimation ausblenden
        loadingDots.style.display = 'none';
        // Antwort des Chatbots im Chatfenster anzeigen
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${data.response}</p>`;
        chatWindow.appendChild(botMessageElement);

        // Speichere die Interaktion in der Datenbank
        saveInteractionToDatabase(currentRiddle, userMessage, data.response);

        chatWindow.scrollTop = chatWindow.scrollHeight;
    })
    .catch(error => console.error('Fehler bei /chat:', error));
}

// Popup-Logik (am Ende des Skripts hinzufügen)
document.querySelectorAll('.hint-area').forEach(hintArea => {
    hintArea.addEventListener('click', function() {
        console.log(`Klick auf ${this.id}`); // Debugging
        const hintId = this.id.replace('-area', '-popup');
        const popup = document.getElementById(hintId);
        if (popup) {
            console.log(`Popup ${hintId} wird angezeigt`); // Debugging
            popup.style.display = 'block';
        }
    });
});

// Event-Listener für das Schriftrollen-Bild
document.querySelector('.scroll-icon').addEventListener('click', function() {
    const popup = document.getElementById('custom-scroll-popup');
    if (popup) {
        popup.style.display = 'flex'; // Popup anzeigen
    }
});

// Event-Listener für das Schließen des Popups
document.querySelector('#custom-scroll-popup .custom-close').addEventListener('click', function() {
    const popup = document.getElementById('custom-scroll-popup');
    if (popup) {
        popup.style.display = 'none'; // Popup ausblenden
    }
});

// Schließe das Popup, wenn außerhalb geklickt wird
window.addEventListener('click', function(event) {
    // Schließe alle Popups, wenn außerhalb geklickt wird
    document.querySelectorAll('.popup').forEach(popup => {
        if (event.target === popup) {
            popup.style.display = 'none'; // Popup ausblenden
        }
    });
    const popup = document.getElementById('custom-scroll-popup');
    if (event.target === popup) {
        popup.style.display = 'none'; // Popup ausblenden
    }
});


document.querySelectorAll('.close').forEach(closeButton => {
    closeButton.addEventListener('click', function() {
        const popup = this.closest('.popup');
        if (popup) {
            popup.style.display = 'none';
        }
    });
});




