// Plain JS on purpose — no build step, no framework. This whole file is
// the only thing that talks to /api/chat; everything else is markup/CSS.

const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const questionEl = document.getElementById("question");
const useRagEl = document.getElementById("use-rag");

function addBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  chatEl.appendChild(bubble);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function addBotAnswer({ answer, used_rag, sources }) {
  const bubble = document.createElement("div");
  bubble.className = "bubble bot";

  const badge = document.createElement("span");
  badge.className = `badge ${used_rag ? "rag" : "no-rag"}`;
  badge.textContent = used_rag ? "Con RAG" : "Sin RAG (Gemini directo)";
  bubble.appendChild(badge);

  const answerText = document.createElement("div");
  answerText.textContent = answer;
  bubble.appendChild(answerText);

  if (used_rag && sources.length > 0) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "sources";
    sourcesEl.textContent = `Fuentes: ${sources.join(", ")}`;
    bubble.appendChild(sourcesEl);
  }

  chatEl.appendChild(bubble);
  chatEl.scrollTop = chatEl.scrollHeight;
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionEl.value.trim();
  if (!question) return;

  addBubble("user", question);
  questionEl.value = "";
  questionEl.disabled = true;
  formEl.querySelector("button").disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, use_rag: useRagEl.checked }),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    addBotAnswer(data);
  } catch (err) {
    addBubble("error", `Error: ${err.message}`);
  } finally {
    questionEl.disabled = false;
    formEl.querySelector("button").disabled = false;
    questionEl.focus();
  }
});
