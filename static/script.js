const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function appendMessage(text, sender, meta = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;

    let contentHtml = `<div class="message-content">${text}</div>`;

    if (meta && sender === 'bot') {
        contentHtml += `
            <div class="meta-info">
                <span class="source-tag">Source: ${meta.source}</span>
                <span>Confidence: ${meta.confidence}</span>
            </div>
        `;
    }

    msgDiv.innerHTML = contentHtml;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add user message
    appendMessage(text, 'user');
    userInput.value = '';

    // Show loading state
    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message';
    loadingDiv.id = loadingId;
    loadingDiv.innerHTML = '<div class="message-content">Thinking...</div>';
    chatHistory.appendChild(loadingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: text })
        });

        const data = await response.json();

        // Remove loading
        document.getElementById(loadingId).remove();

        if (data.error) {
            appendMessage("Error: " + data.error, 'bot');
        } else {
            appendMessage(data.answer, 'bot', {
                source: data.source,
                confidence: data.confidence
            });
        }

    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage("Sorry, I couldn't reach the server.", 'bot');
        console.error(error);
    }
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
