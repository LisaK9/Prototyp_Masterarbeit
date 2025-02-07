const correctCode = [6, 2, 4]; // Der richtige Code: 6-2-4

let lastRiddle = 1;  // Speichert das zuletzt aktive Rätsel

function checkDigit(digitIndex) {
    const input = document.getElementById(`code-digit-${digitIndex}`);
    const feedback = document.getElementById('code-feedback');
    const enteredDigit = input.value.trim();

    // Prüfen, ob die Eingabe eine Zahl ist
    if (enteredDigit && isNaN(enteredDigit)) {
        feedback.textContent = `Bitte eine gültige Zahl (0-9) eingeben.`;
        feedback.style.color = 'red';
        input.value = '';
        return;
    }

    // Automatisch zum nächsten Eingabefeld springen
    if (digitIndex < 3 && enteredDigit) {
        document.getElementById(`code-digit-${digitIndex + 1}`).disabled = false;
        document.getElementById(`code-digit-${digitIndex + 1}`).focus();
    }

    // Aktuellen Code aus den Eingabefeldern lesen
    const digit1 = document.getElementById('code-digit-1').value || "_";
    const digit2 = document.getElementById('code-digit-2').value || "_";
    const digit3 = document.getElementById('code-digit-3').value || "_";

    fetch('/update_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ digit1, digit2, digit3 })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Aktuelles Rätsel:", data.current_riddle);

        // Falls alle Zahlen eingegeben wurden, falsche Zahlen löschen
        if (digit1 !== "_" && digit2 !== "_" && digit3 !== "_") {
            if (digit1 !== data.code[0]) document.getElementById('code-digit-1').value = "";
            if (digit2 !== data.code[1]) document.getElementById('code-digit-2').value = "";
            if (digit3 !== data.code[2]) document.getElementById('code-digit-3').value = "";

            // Falls der Code richtig ist, Erfolgsmeldung anzeigen
            if (data.current_riddle === 4) {
                feedback.textContent = "Code erfolgreich eingegeben!";
                feedback.style.color = 'green';
            } else {
                feedback.textContent = "Einige Zahlen waren falsch. Versuche es erneut!";
                feedback.style.color = 'red';
            }
        }

        lastRiddle = data.current_riddle; // Speichert den aktuellen Fortschritt
    })
    .catch(error => console.error('Error bei /update_code:', error));
}

// **Funktion zum Senden einer Nachricht an den Chatbot**
function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const userMessage = chatInput.value.trim();

    if (!userMessage) return;  // Keine Nachricht senden, wenn das Eingabefeld leer ist

    // Benutzernachricht im Chatfenster anzeigen
    const userMessageElement = document.createElement('div');
    userMessageElement.classList.add('message', 'user');
    userMessageElement.innerHTML = `<p>${userMessage}</p>`;
    chatWindow.appendChild(userMessageElement);

    chatInput.value = '';  // Eingabefeld leeren
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Nachricht an den Chatbot senden
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Antwort des Chatbots im Chatfenster anzeigen
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${data.response}</p>`;
        chatWindow.appendChild(botMessageElement);

        chatWindow.scrollTop = chatWindow.scrollHeight;
    })
    .catch(error => console.error('Fehler bei /chat:', error));
}

// **Event-Listener für die Eingabefelder**
document.getElementById('code-digit-1').addEventListener('input', function() {
    checkDigit(1);
});

document.getElementById('code-digit-2').addEventListener('input', function() {
    checkDigit(2);
});

document.getElementById('code-digit-3').addEventListener('input', function() {
    checkDigit(3);
});

// **Event-Listener für die Enter-Taste im Chat-Eingabefeld**
document.getElementById('chat-input')?.addEventListener('keydown', function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

function toggleChat() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.classList.toggle('active');
}

function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const userMessage = chatInput.value.trim();

    if (!userMessage) return;

    // Benutzernachricht im Chatfenster anzeigen
    const userMessageElement = document.createElement('div');
    userMessageElement.classList.add('message', 'user');
    userMessageElement.innerHTML = `<p>${userMessage}</p>`;
    chatWindow.appendChild(userMessageElement);

    chatInput.value = '';
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Nachricht an den Chatbot senden
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Antwort des Chatbots im Chatfenster anzeigen
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot');
        botMessageElement.innerHTML = `<p>${data.response}</p>`;
        chatWindow.appendChild(botMessageElement);

        chatWindow.scrollTop = chatWindow.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);

        // Fehlermeldung im Chatfenster anzeigen
        const errorMessageElement = document.createElement('div');
        errorMessageElement.classList.add('message', 'bot');
        errorMessageElement.innerHTML = `<p>Sorry, something went wrong.</p>`;
        chatWindow.appendChild(errorMessageElement);

        chatWindow.scrollTop = chatWindow.scrollHeight;
    });
}

// Event-Listener für die Enter-Taste hinzufügen
document.getElementById('chat-input').addEventListener('keydown', function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

// Bild einblenden
function revealImage(imageId) {
    const popup = document.getElementById(imageId);
    const overlay = document.getElementById('popup-overlay');

    // Bild und Overlay anzeigen
    popup.style.display = 'block';
    overlay.style.display = 'block';
}

// Bild ausblenden
function closeImage(imageId) {
    const popup = document.getElementById(imageId);
    const overlay = document.getElementById('popup-overlay');

    // Bild und Overlay ausblenden
    popup.style.display = 'none';
    overlay.style.display = 'none';
}

// Schließen durch Klick auf das Overlay
document.getElementById('popup-overlay').addEventListener('click', () => {
    const popups = document.querySelectorAll('.popup');
    popups.forEach(popup => popup.style.display = 'none');

    const overlay = document.getElementById('popup-overlay');
    overlay.style.display = 'none';
});

// Schriftrollen-Popup öffnen
function openScrollPopup() {
    const popup = document.getElementById('scroll-popup');
    const overlay = document.getElementById('scroll-popup-overlay');

    // Popup und Overlay anzeigen
    popup.style.display = 'block';
    overlay.style.display = 'block';
}

// Schriftrollen-Popup schließen
function closeScrollPopup() {
    const popup = document.getElementById('scroll-popup');
    const overlay = document.getElementById('scroll-popup-overlay');

    // Popup und Overlay ausblenden
    popup.style.display = 'none';
    overlay.style.display = 'none';
}

// Schließen durch Klick auf das Overlay
document.getElementById('scroll-popup-overlay').addEventListener('click', () => {
    closeScrollPopup();
});