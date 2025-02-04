const correctCode = [6, 2, 4]; // Der richtige Code: 6-2-4

function checkDigit(digitIndex) {
    const input = document.getElementById(`code-digit-${digitIndex}`);
    const feedback = document.getElementById('code-feedback');
    const enteredDigit = parseInt(input.value, 10);

    // Überprüfen, ob die Eingabe eine Zahl ist
    if (isNaN(enteredDigit)) {
        feedback.textContent = `Please enter a valid digit (0-9).`;
        feedback.style.color = 'red';
        input.value = ''; // Eingabefeld leeren
        return;
    }

    // das nächste Eingabefeld aktivieren
    if (digitIndex < 3) {
        const nextInput = document.getElementById(`code-digit-${digitIndex + 1}`);
        nextInput.disabled = false;
        nextInput.focus();
    }

    // Überprüfen, ob alle drei Zahlen eingegeben wurden
    const digit1 = document.getElementById('code-digit-1').value;
    const digit2 = document.getElementById('code-digit-2').value;
    const digit3 = document.getElementById('code-digit-3').value;

    if (digit1 && digit2 && digit3) {
        // Alle drei Zahlen sind eingegeben
        if (digit1 == correctCode[0] && digit2 == correctCode[1] && digit3 == correctCode[2]) {
            feedback.textContent = 'Code accepted! The secret is unlocked.';
            feedback.style.color = 'green';
        } else {
            feedback.textContent = 'Incorrect code. Please try again.';
            feedback.style.color = 'red';

            // alle falschen Zahlen löschen
            if (digit1 != correctCode[0]) {
                document.getElementById('code-digit-1').value = '';
            }
            if (digit2 != correctCode[1]) {
                document.getElementById('code-digit-2').value = '';
            }
            if (digit3 != correctCode[2]) {
                document.getElementById('code-digit-3').value = '';
            }

            // Fokus zurück auf das erste falsche Feld setzen
            if (digit1 != correctCode[0]) {
                document.getElementById('code-digit-1').focus();
            } else if (digit2 != correctCode[1]) {
                document.getElementById('code-digit-2').focus();
            } else if (digit3 != correctCode[2]) {
                document.getElementById('code-digit-3').focus();
            }
        }

        // aktuellen Fortschritt an den Server senden
        fetch('/update_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                digit1: digit1,
                digit2: digit2,
                digit3: digit3
            })
        });
    }
}

// Event-Listener für die Eingabefelder
document.getElementById('code-digit-1').addEventListener('input', function() {
    checkDigit(1);
});

document.getElementById('code-digit-2').addEventListener('input', function() {
    checkDigit(2);
});

document.getElementById('code-digit-3').addEventListener('input', function() {
    checkDigit(3);
});

function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const typingIndicator = document.getElementById('typing-indicator');
    const userMessage = chatInput.value.trim();

    if (!userMessage) return;

    // Benutzernachricht im Chatfenster zeigen
    chatWindow.innerHTML += `<p><strong>You:</strong> ${userMessage}</p>`;
    chatInput.value = '';

    // Typing Indicator anzeigen
    typingIndicator.style.display = 'block';
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
        // Typing Indicator verstecken
        typingIndicator.style.display = 'none';

        // Antwort des Chatbots im Chatfenster anzeigen
        chatWindow.innerHTML += `<p><strong>Bot:</strong> ${data.response}</p>`;
        chatWindow.scrollTop = chatWindow.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);

        // Typing Indicator verstecken
        typingIndicator.style.display = 'none';

        // Fehlermeldung im Chatfenster anzeigen
        chatWindow.innerHTML += `<p><strong>Bot:</strong> Sorry, something went wrong.</p>`;
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