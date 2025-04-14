const correctCode = [9, 2];

let currentRiddle = 1;
let allowPageUnload = false; // Standardmäßig keine Erlaubnis zum Verlassen
let solutionStepShown = 0;
// erstes Eingabefeld beim Laden der Seite aktivieren
document.getElementById('code-digit-1').disabled = false;
document.getElementById('code-digit-1').focus();

// Funktion zum Aktualisieren der Klickbarkeit der Hinweise
function updateHintAreas(currentRiddle) {
    // alle Hinweisflächen zunächst deaktivieren
    document.querySelectorAll('.hint-area').forEach(hintArea => {
        hintArea.style.pointerEvents = 'none';
    });

    // Hinweisflächen basierend auf dem aktuellen Rätsel aktivieren
    if (currentRiddle === 1) {
        // Hinweise für Rätsel 1
        document.getElementById('hint1-area').style.pointerEvents = 'auto';
        document.getElementById('hint2-area').style.pointerEvents = 'auto';
        document.getElementById('hint3-area').style.pointerEvents = 'auto';
        document.getElementById('hint4-area').style.pointerEvents = 'auto';
    }
}


document.addEventListener('DOMContentLoaded', function() {
    updateHintAreas(currentRiddle);
});

let sessionId;  // Globale Variable für die Session-ID

// Anzahl der Versuche für jedes Rätsel
const attemptsTracker = {
    1: 0, // Versuche für Rätsel 1
    2: 0, // Versuche für Rätsel 2
};
//Startzeit für jedes Rätsel
const startTimes = {
    1: null, // Startzeit für Rätsel 1
    2: null, // Startzeit für Rätsel 2
};
//Botanfragen für jedes Rätsel
const botRequestCounts = {
    1: 0, // Bot-Anfragen für Rätsel 1
    2: 0, // Bot-Anfragen für Rätsel 2
};

// Funktion zum Starten einer neuen Session
function startSession() {
    fetch('/start_session', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        sessionId = data.session_id;
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
            attempts_riddle_2: attemptsTracker[2]
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
        chestImage.style.cursor = 'pointer';
        chestImage.addEventListener('click', function() {
            // Überprüfen, ob der gesamte Code korrekt eingegeben wurde
            if (currentRiddle === 1 && attemptsTracker[1] > 0) {
                allowPageUnload = true;
                // neue HTML-Seite
                window.location.href = '/geheimnis';
            }
        });
    }
}

function checkDigit() {
    const input = document.getElementById(`code-digit-${currentRiddle}`);
    const feedback = document.getElementById('code-feedback');
    const enteredDigit = input.value.trim();

    // Versuchszähler für das aktuelle Rätsel erhöhen
    attemptsTracker[currentRiddle]++;

    // eingegebene Zahl zur Überprüfung senden
    fetch('/update_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ digit: enteredDigit, riddle_number: currentRiddle })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "correct") {


            // benötigte Zeit für das Rätsel berechnen
            const endTime = new Date();  // Aktuelle Zeit als Date-Objekt
            const timeTaken = Math.floor((endTime - startTimes[currentRiddle]) / 1000); // Zeit in Sekunden

            // Zeit in der Datenbank speichern
            saveTimeToDatabase(currentRiddle, timeTaken, startTimes[currentRiddle], endTime);

            // Bot-Anfragen in der Datenbank speichern
            saveBotRequestsToDatabase(currentRiddle, botRequestCounts[currentRiddle]);

            // Chatbot Feedback
            sendChatbotFeedback(currentRiddle);

            input.disabled = true;



            // Versuche in der Datenbank speichern
            saveAttemptsToDatabase();
            makeChestClickable();

        } else {

            input.value = '';
            input.focus();

            sendChatbotWrongAnswerFeedback();
        }
    })
    .catch(error => console.error('Error bei /update_code:', error));
}

// neue Session, wenn das Spiel geladen wird
document.addEventListener('DOMContentLoaded', function() {
    startSession();
    updateHintAreas(currentRiddle);

    // Startzeit für Rätsel 1 setzen, sobald die Seite geladen wird
    if (!startTimes[1]) {
        startTimes[1] = new Date();  // Startzeit für Rätsel 1 setzen
        console.log('Startzeit für Rätsel 1 gesetzt:', startTimes[1]);
    }

    // Begrüßungsnachricht im Chatfenster anzeigen
    const chatWindow = document.getElementById('chat-window');
    const botMessageElement = document.createElement('div');
    botMessageElement.classList.add('message', 'bot');
    botMessageElement.innerHTML = `<p>Willkommen! Ich bin Einar, ein Nachfahre der Wikinger. Während des Rätsels stehe ich dir mit Rat und Herz zur Seite. Schau dir am besten zunächst den Hinweis in der Schriftrolle an, die du bereits gefunden hast.</p>`;
    chatWindow.appendChild(botMessageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight;
});

// Event-Listener für die Eingabefelder, um die Entertaste zu unterstützen
document.querySelectorAll('#code-input input').forEach(input => {
    input.addEventListener('keydown', function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            checkDigit();
        }
    });
});

// Funktion, um Feedback vom Chatbot anzuzeigen, wenn ein Rätsel gelöst wurde
function sendChatbotFeedback(riddleNumber) {
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');

    // Feedback-Nachrichten für jedes Rätsel
    const feedbackMessages = {
        1: "Hah! Du hast die Zeichen der Ahnen verstanden! Nur die Klugen und Weisen erkennen das verborgene Muster. Ich spüre, dass du den Geist eines echten Skalden in dir trägst! Öffne nun die Truhe und entdecke, was in ihrem Inneren auf dich wartet."

    };

    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    // kurze Verzögerung, bevor die Nachricht angezeigt wird
    setTimeout(() => {
        // Ladeanimation ausblenden
        loadingDots.style.display = 'none';

        // Feedback-Nachricht des Chatbots
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${feedbackMessages[riddleNumber]}</p>`;
        chatWindow.appendChild(botMessageElement);


        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 1000); // 1 Sekunde Verzögerung
}

// Funktion, um zufälliges Feedback für eine falsche Antwort zu geben
function sendChatbotWrongAnswerFeedback() {
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');

    // Feedback-Nachrichten für falsche Antworten
    const wrongAnswerMessages = [
        "Oh je... das war nicht ganz richtig. Aber weißt du was? Ich glaube fest an dich – du schaffst das beim nächsten Versuch!",
        "Nicht ganz, aber gib nicht auf! Die Wikinger waren auch hartnäckig.",
        "Autsch! Das war daneben – aber kein Kampf ist je beim ersten Schlag gewonnen worden!",
        "Das war leider nicht die richtige Zahl... Aber hey – wir kommen der Lösung immer näher!",
        "Ach, daneben! Ich war mir so sicher… Aber Fehler gehören dazu, oder? Versuch’s nochmal."
    ];

    // zufällige Nachricht aus der Liste auswählen
    const randomMessage = wrongAnswerMessages[Math.floor(Math.random() * wrongAnswerMessages.length)];

    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    // kurze Verzögerung, bevor die Nachricht angezeigt wird
    setTimeout(() => {
        // Ladeanimation ausblenden
        loadingDots.style.display = 'none';

        // zufällige Feedback-Nachricht des Chatbots
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${randomMessage}</p>`;
        chatWindow.appendChild(botMessageElement);


        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 1000); // 1 Sekunde Verzögerung
}



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

// Funktion zum Senden einer Nachricht an den Chatbot
function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const loadingDots = document.getElementById('loading-dots');
    const userMessage = chatInput.value.trim();

    if (!userMessage) return;  // Keine Nachricht senden, wenn das Eingabefeld leer ist

    // Zähler für Bot-Anfragen erhöhen
    botRequestCounts[currentRiddle]++;

    // Benutzernachricht im Chatfenster anzeigen
    const userMessageElement = document.createElement('div');
    userMessageElement.classList.add('message', 'user');
    userMessageElement.innerHTML = `<p>${userMessage}</p>`;
    chatWindow.appendChild(userMessageElement);

    chatInput.value = '';  // Eingabefeld leeren


    // Ladeanimation anzeigen
    loadingDots.style.display = 'flex';

    chatWindow.scrollTop = chatWindow.scrollHeight;

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

        // Interaktion in der Datenbank speichern
        saveInteractionToDatabase(currentRiddle, userMessage, data.response);

        chatWindow.scrollTop = chatWindow.scrollHeight;
    })
    .catch(error => console.error('Fehler bei /chat:', error));
}

// Popup-Logik
document.querySelectorAll('.hint-area').forEach(hintArea => {
    hintArea.addEventListener('click', function() {
        console.log(`Klick auf ${this.id}`); // Debugging
        const hintId = this.id.replace('-area', '-popup');
        const popup = document.getElementById(hintId);
        if (popup) {
            console.log(`Popup ${hintId} wird angezeigt`); // Debugging
            popup.style.display = 'block';
        }
        const hintNumber = parseInt(this.id.replace('hint', '').replace('-area', ''));
        // Klick in der Datenbank speichern
        fetch('/save_hint_click', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                hint_number: hintNumber
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(`Hinweis ${hintNumber} Klick gespeichert:`, data);
        })
        .catch(error => console.error('Fehler beim Speichern des Hinweisklicks:', error));
    });
});



// Event-Listener für das Schriftrollen-Bild
document.querySelector('.scroll-icon').addEventListener('click', function() {
    const popup = document.getElementById('custom-scroll-popup');
    if (popup) {
        popup.style.display = 'flex'; // Popup anzeigen
    }
});

document.getElementById('lösung-button').addEventListener('click', function () {
    if (botRequestCounts[currentRiddle] >= 3) {

        const popup = document.getElementById('lösungpopup');
        if (popup) {
            popup.style.display = 'flex';

            document.querySelectorAll('.lösung-scroll-text').forEach(text => {
                text.style.display = 'none';
            });

            const solutionText = document.getElementById(`lösung${currentRiddle}`);
            if (solutionText) {
                solutionText.style.display = 'block';
            }

            const steps = document.querySelectorAll(`#lösung${currentRiddle} .lösung-step`);

            // Beim ersten Öffnen: initialisieren & Schritt 1 speichern
            if (typeof solutionStepShown === 'undefined' || solutionStepShown === null) {
                solutionStepShown = 0;
                fetch('/save_solution_step', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        riddle_number: currentRiddle,
                        step_number: 1
                    })
                });
            }

            // Alle bis dahin gesehenen Schritte anzeigen
            for (let i = 0; i <= solutionStepShown; i++) {
                if (steps[i]) steps[i].style.display = 'block';
            }

            // Weiter-Button anzeigen, wenn noch Schritte da sind
            const nextButton = document.getElementById('lösung-next-button');
            if (solutionStepShown < steps.length - 1) {
                nextButton.style.display = 'block';
            } else {
                nextButton.style.display = 'none';
            }

            // Lösung als "gesehen" speichern (wie bisher)
            fetch('/view_solution', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    riddle_number: currentRiddle
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Lösungsstatus gespeichert:', data);
            })
            .catch(error => console.error('Fehler beim Speichern des Lösungsstatus:', error));
        }

    } else {
        alert('Du musst mindestens 3 Bot-Anfragen stellen, bevor du die Lösung sehen kannst.');
    }
});

// Event-Listener für das Schließen des Lösungs-Popups
document.querySelector('#lösungpopup .custom-close').addEventListener('click', function() {
    const popup = document.getElementById('lösungpopup');
    if (popup) {
        popup.style.display = 'none'; // Popup ausblenden
    }
});

// Popup schließen, wenn außerhalb geklickt wird
window.addEventListener('click', function(event) {
    const popup = document.getElementById('lösungpopup');
    if (event.target === popup) {
        popup.style.display = 'none'; // Popup ausblenden
    }
});

// Event-Listener für das Schließen des Popups
document.querySelector('#custom-scroll-popup .custom-close').addEventListener('click', function() {
    const popup = document.getElementById('custom-scroll-popup');
    if (popup) {
        popup.style.display = 'none'; // Popup ausblenden
    }
});

// Popup schließen, wenn außerhalb geklickt wird
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

window.onbeforeunload = function () {
    if (!allowPageUnload) {
        return "Wenn du die Seite verlässt oder neu lädst, verlierst du deinen Fortschritt!";
    }
};


document.getElementById('lösung-next-button').addEventListener('click', function () {
    const steps = document.querySelectorAll(`#lösung${currentRiddle} .lösung-step`);

    if (solutionStepShown < steps.length - 1) {
        solutionStepShown++;
        steps[solutionStepShown].style.display = 'block';

        // Speichern, welcher Schritt angezeigt wurde
        fetch('/save_solution_step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                riddle_number: currentRiddle,
                step_number: solutionStepShown + 1
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(`Lösungsschritt ${solutionStepShown + 1} gespeichert:`, data);
        })
        .catch(error => console.error('Fehler beim Speichern des Lösungsschritts:', error));

        if (solutionStepShown === steps.length - 1) {
            this.style.display = 'none'; // Letzter Schritt erreicht
        }
    }
});

