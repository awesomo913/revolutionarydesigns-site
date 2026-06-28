export async function submitSignup(fetchFn, workerUrl, payload) {
  try {
    const res = await fetchFn(workerUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.status === 200) {
      const blob = await res.blob();
      return { ok: true, blob };
    }
    let message = "Couldn't send right now. Please try again.";
    try {
      const data = await res.json();
      if (data && data.error) message = data.error;
    } catch (_) {}
    return { ok: false, message };
  } catch (_) {
    return { ok: false, message: "Couldn't reach the server. Check your connection and try again." };
  }
}

// Browser bootstrap (ignored by the node test, which only imports submitSignup).
if (typeof document !== "undefined") {
  const WORKER_URL = "https://cactus-email-worker.revodesigns.workers.dev/subscribe";
  const form = document.getElementById("gcform");
  if (form) {
    const card = document.getElementById("gccard");
    const ok = document.getElementById("gcok");
    const errEl = document.getElementById("gcerr");
    const consent = document.getElementById("gcconsent-input");
    const emailEl = document.getElementById("gcemail");
    const hp = document.getElementById("gcwebsite");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      errEl.textContent = "";
      if (!consent.checked) { errEl.textContent = "Please tick the consent box to continue."; return; }
      const payload = { email: emailEl.value, consent: consent.checked, source: "cactus-codex", website: hp.value };
      const result = await submitSignup(window.fetch.bind(window), WORKER_URL, payload);
      if (result.ok) {
        const url = URL.createObjectURL(result.blob);
        const a = document.createElement("a");
        a.href = url; a.download = "cactus-starter-guide.pdf";
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
        card.style.display = "none";
        ok.style.display = "block";
      } else {
        errEl.textContent = result.message;
      }
    });
  }
}
