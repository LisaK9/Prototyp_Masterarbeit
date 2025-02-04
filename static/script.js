document.getElementById("sendButton").addEventListener("click", () => {
    const userInput = document.getElementById("userInput").value;
    if (userInput.trim() === "") return;

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userInput }),
    })
        .then(response => response.json())
        .then(data => {
            const messagesDiv = document.getElementById("messages");

            // Nutzereingabe anzeigen
            const userMessage = document.createElement("div");
            userMessage.textContent = `Spieler: ${userInput}`;
            messagesDiv.appendChild(userMessage);

            // Antwort des Chatbots anzeigen
            const botMessage = document.createElement("div");
            botMessage.textContent = `KI-Bibliothekar: ${data.response}`;
            messagesDiv.appendChild(botMessage);

            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        });

    document.getElementById("userInput").value = "";
});
