const TOKEN_KEY = "fi_notes_access_token";
const REFRESH_KEY = "fi_notes_refresh_token";
const EMAIL_KEY = "fi_notes_user_email";
const THEME_KEY = "fi_notes_theme";
let googleOAuthEnabled = false;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "light") {
    document.body.classList.add("light-mode");
  } else if (!saved && window.matchMedia("(prefers-color-scheme: light)").matches) {
    document.body.classList.add("light-mode");
  }
}

function toggleTheme() {
  console.log("Toggling theme...");
  const isLight = document.body.classList.toggle("light-mode");
  localStorage.setItem(THEME_KEY, isLight ? "light" : "dark");
  console.log("New theme is:", isLight ? "light" : "dark");
}

async function transliterate(text) {
  if (!text.trim()) return text;
  try {
    const res = await fetch(`https://inputtools.google.com/request?text=${encodeURIComponent(text)}&itc=hi-t-i0-und&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8&app=test`);
    const data = await res.json();
    if (data[0] === "SUCCESS") {
      return data[1][0][1][0] || text;
    }
  } catch (err) {
    console.error("Transliteration failed:", err);
  }
  return text;
}

async function handleHindiInput(e) {
  if (!$("#hindi-toggle")?.checked) return;
  
  if (e.key === " " || e.key === "Enter") {
    const textarea = e.target;
    const text = textarea.value;
    const cursor = textarea.selectionStart;
    
    // Find the word right before the cursor (the word we just finished typing)
    const textBeforeCursor = text.substring(0, cursor - 1);
    const words = textBeforeCursor.split(/[\s\n]+/);
    const lastWord = words[words.length - 1];
    
    // Only transliterate if it's an English word
    if (lastWord && /^[a-zA-Z]+$/.test(lastWord)) {
      const hindiWord = await transliterate(lastWord);
      if (hindiWord !== lastWord) {
        const start = cursor - 1 - lastWord.length;
        const newValue = text.substring(0, start) + hindiWord + text.substring(cursor - 1);
        textarea.value = newValue;
        // Move cursor back to after the inserted hindi word + the space/enter
        const newCursorPos = start + hindiWord.length + 1;
        textarea.selectionStart = textarea.selectionEnd = newCursorPos;
      }
    }
  }
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setSession(accessToken, email, refreshToken = null) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(EMAIL_KEY, email);
  if (refreshToken) {
    localStorage.setItem(REFRESH_KEY, refreshToken);
  }
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const data = await api("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refresh }),
    });
    setSession(data.access_token, localStorage.getItem(EMAIL_KEY), data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

function parseError(data) {
  if (!data) return "Something went wrong";
  if (data.message) return data.message;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => e.msg || JSON.stringify(e)).join(", ");
  }
  return "Request failed";
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(path, { ...options, headers });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!res.ok) {
    if (
      res.status === 401 &&
      token &&
      !path.includes("/auth/refresh") &&
      !path.includes("/login")
    ) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return api(path, options);
      }
      clearSession();
    }
    const err = new Error(parseError(data));
    err.status = res.status;
    err.data = data;
    throw err;
  }

  if (res.status === 204) return null;
  return data;
}

function showAlert(el, message, type = "error") {
  el.className = `alert alert-${type}`;
  el.textContent = message;
  el.classList.remove("hidden");
}

function hideAlert(el) {
  el.classList.add("hidden");
  el.textContent = "";
}

function formatDate(iso) {
  if (!iso) return "";
  // Ensure the string is treated as UTC if it lacks timezone info
  let dateStr = iso;
  if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
    dateStr += 'Z';
  }
  const d = new Date(dateStr);
  return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function showGuestView() {
  $("#view-guest").classList.remove("hidden");
  $("#view-app").classList.add("hidden");
  $("#user-badge").classList.add("hidden");
  $("#btn-logout").classList.add("hidden");
  showAuthForms();
}

function showAppView() {
  $("#view-guest").classList.add("hidden");
  $("#view-app").classList.remove("hidden");
  const email = localStorage.getItem(EMAIL_KEY) || "Signed in";
  $("#user-badge").textContent = email;
  $("#user-badge").classList.remove("hidden");
  $("#btn-logout").classList.remove("hidden");
}

function openModal(id) {
  $(`#${id}`).classList.remove("hidden");
}

function closeModal(id) {
  $(`#${id}`).classList.add("hidden");
  const alert = document.getElementById(`${id}-alert`);
  if (alert) hideAlert(alert);
}

function switchAuthTab(tab) {
  $$(".auth-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  $("#form-login").classList.toggle("hidden", tab !== "login");
  $("#form-register").classList.toggle("hidden", tab !== "register");
  hideAlert($("#auth-alert"));
}

function showVerifyStep(email, otp = null) {
  $("#auth-tabs").classList.add("hidden");
  $("#auth-forms").classList.add("hidden");
  $("#btn-google").classList.add("hidden");
  document.querySelector(".auth-divider")?.classList.add("hidden");
  $("#google-setup-note").classList.add("hidden");
  $("#auth-setup-hints").classList.add("hidden");
  $("#form-verify").classList.remove("hidden");
  $("#verify-email").value = email;
  $("#verify-email-display").textContent = email;
  $("#verify-otp").value = "";
  showOtpCode(otp);
  hideAlert($("#auth-alert"));
}

function showAuthForms() {
  $("#auth-tabs").classList.remove("hidden");
  $("#auth-forms").classList.remove("hidden");
  $("#form-verify").classList.add("hidden");
  $("#btn-google").classList.remove("hidden");
  document.querySelector(".auth-divider")?.classList.remove("hidden");
  showOtpCode(null);
  loadAuthStatus();
}

function showOtpCode(otp) {
  if (!otp) {
    $("#otp-display").classList.add("hidden");
    return;
  }
  $("#otp-code").textContent = otp;
  $("#otp-display").classList.remove("hidden");
}

async function loadAuthStatus() {
  try {
    const status = await api("/auth/status");
    const hintsEl = $("#auth-setup-hints");
    const googleBtn = $("#btn-google");

    if (hintsEl) {
      hintsEl.innerHTML = "";
      hintsEl.classList.add("hidden");
      if (!status.smtp_configured && status.smtp_setup_hint) {
        hintsEl.innerHTML = `<p>${status.smtp_setup_hint}</p>`;
        hintsEl.classList.remove("hidden");
      }
    }

    googleOAuthEnabled = status.google_oauth_enabled;
    if (googleBtn) {
      if (googleOAuthEnabled) {
        googleBtn.classList.remove("btn-disabled");
      } else {
        googleBtn.classList.add("btn-disabled");
      }
    }
  } catch (err) {
    console.error("Failed to load auth status:", err);
  }
}

function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  const email = params.get("email");
  const authError = params.get("auth_error");

  if (authError) {
    showGuestView();
    const messages = {
      google_not_configured: "Google sign-in is not configured on the server.",
      google_auth_failed: "Google sign-in was cancelled or failed.",
      missing_user_info: "Could not read your Google profile.",
      invalid_google_profile: "Invalid Google account information.",
    };
    showAlert($("#auth-alert"), messages[authError] || "Sign-in failed", "error");
    window.history.replaceState({}, "", "/");
    return;
  }

  const refresh = params.get("refresh_token");
  if (token && email) {
    setSession(token, email, refresh);
    window.history.replaceState({}, "", "/");
    showAppView();
    loadNotes();
  }
}

async function completeLogin(data, email) {
  setSession(data.access_token, email, data.refresh_token);
  showAppView();
  await loadNotes();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadNotes() {
  const alertEl = $("#notes-alert");
  hideAlert(alertEl);

  try {
    const notes = await api("/notes");
    renderNotes(notes);
  } catch (err) {
    if (err.status === 401) {
      clearSession();
      showGuestView();
      return;
    }
    showAlert(alertEl, err.message);
  }
}

function renderNotes(notes) {
  const grid = $("#notes-grid");
  const empty = $("#notes-empty");

  if (!notes.length) {
    grid.classList.add("hidden");
    grid.innerHTML = "";
    empty.classList.remove("hidden");
    return;
  }

  empty.classList.add("hidden");
  grid.classList.remove("hidden");
  grid.innerHTML = notes
    .map(
      (note) => `
    <article class="note-card" data-id="${note.id}">
      <h3>${escapeHtml(note.title)}</h3>
      <p class="content-preview">${escapeHtml(note.content)}</p>
      <p class="note-meta">Updated ${formatDate(note.updated_at)}</p>
      <div class="note-actions">
        <button type="button" class="btn btn-secondary btn-sm btn-edit" data-id="${note.id}">Edit</button>
        <button type="button" class="btn btn-secondary btn-sm btn-share" data-id="${note.id}">Share</button>
        <button type="button" class="btn btn-danger btn-sm btn-delete" data-id="${note.id}">Delete</button>
      </div>
    </article>
  `
    )
    .join("");

  grid.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.addEventListener("click", () => openEditNote(Number(btn.dataset.id)));
  });
  grid.querySelectorAll(".btn-share").forEach((btn) => {
    btn.addEventListener("click", () => openShareNote(Number(btn.dataset.id)));
  });
  grid.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.addEventListener("click", () => deleteNote(Number(btn.dataset.id)));
  });
}



function openNewNote() {
  $("#modal-note-heading").textContent = "New note";
  $("#note-id").value = "";
  $("#note-title").value = "";
  $("#note-content").value = "";
  if ($("#hindi-toggle")) $("#hindi-toggle").checked = false;
  $("#hindi-hint")?.classList.add("hidden");
  hideAlert($("#modal-note-alert"));
  openModal("modal-note");
}

async function openEditNote(id) {
  hideAlert($("#modal-note-alert"));
  try {
    const note = await api(`/notes/${id}`);
    $("#modal-note-heading").textContent = "Edit note";
    $("#note-id").value = note.id;
    $("#note-title").value = note.title;
    $("#note-content").value = note.content;
    if ($("#hindi-toggle")) $("#hindi-toggle").checked = false;
    $("#hindi-hint")?.classList.add("hidden");
    openModal("modal-note");
  } catch (err) {
    showAlert($("#notes-alert"), err.message);
  }
}

function openShareNote(id) {
  $("#share-note-id").value = id;
  $("#share-email").value = "";
  hideAlert($("#modal-share-alert"));
  openModal("modal-share");
}

async function deleteNote(id) {
  if (!confirm("Delete this note permanently?")) return;
  try {
    await api(`/notes/${id}`, { method: "DELETE" });
    await loadNotes();
  } catch (err) {
    showAlert($("#notes-alert"), err.message);
  }
}

$("#btn-google").addEventListener("click", (e) => {
  if (!googleOAuthEnabled) {
    e.preventDefault();
    showAlert(
      $("#auth-alert"),
      "Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env, then restart the server.",
      "error"
    );
  }
});

$$(".auth-tab").forEach((btn) => {
  btn.addEventListener("click", () => switchAuthTab(btn.dataset.tab));
});

$("#form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const alertEl = $("#auth-alert");
  hideAlert(alertEl);
  const email = $("#login-email").value.trim().toLowerCase();
  const password = $("#login-password").value;

  try {
    const data = await api("/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    await completeLogin(data, email);
  } catch (err) {
    if (err.status === 403 && err.data?.requires_verification) {
      showVerifyStep(err.data.email || email, err.data.otp || null);
      showAlert(alertEl, err.message, "success");
      return;
    }
    showAlert(alertEl, err.message);
  }
});

$("#form-register").addEventListener("submit", async (e) => {
  e.preventDefault();
  const alertEl = $("#auth-alert");
  hideAlert(alertEl);
  const email = $("#reg-email").value.trim().toLowerCase();
  const password = $("#reg-password").value;
  const full_name = $("#reg-name").value.trim() || null;

  try {
    const data = await api("/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
    showAlert(alertEl, data.message, "success");
    showVerifyStep(email, data.otp || null);
  } catch (err) {
    showAlert(alertEl, err.message);
  }
});

$("#form-verify").addEventListener("submit", async (e) => {
  e.preventDefault();
  const alertEl = $("#auth-alert");
  hideAlert(alertEl);
  const email = $("#verify-email").value;
  const otp = $("#verify-otp").value.trim();

  try {
    const data = await api("/verify-otp", {
      method: "POST",
      body: JSON.stringify({ email, otp }),
    });
    await completeLogin(data, email);
  } catch (err) {
    showAlert(alertEl, err.message);
  }
});

$("#btn-resend-otp").addEventListener("click", async () => {
  const alertEl = $("#auth-alert");
  hideAlert(alertEl);
  const email = $("#verify-email").value;
  try {
    const data = await api("/resend-otp", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    showAlert(alertEl, data.message, "success");
    showOtpCode(data.otp || null);
  } catch (err) {
    showAlert(alertEl, err.message);
  }
});

$("#btn-back-auth").addEventListener("click", () => {
  showAuthForms();
  switchAuthTab("login");
});

$("#btn-logout").addEventListener("click", () => {
  clearSession();
  showGuestView();
});

$("#btn-new-note").addEventListener("click", openNewNote);
$("#btn-empty-create").addEventListener("click", openNewNote);

$("#form-note").addEventListener("submit", async (e) => {
  e.preventDefault();
  const alertEl = $("#modal-note-alert");
  hideAlert(alertEl);

  const id = $("#note-id").value;
  const title = $("#note-title").value.trim();
  const content = $("#note-content").value.trim();
  const body = JSON.stringify({ title, content });

  try {
    if (id) {
      await api(`/notes/${id}`, { method: "PUT", body });
    } else {
      await api("/notes", { method: "POST", body });
    }
    closeModal("modal-note");
    await loadNotes();
  } catch (err) {
    showAlert(alertEl, err.message);
  }
});

$("#form-share").addEventListener("submit", async (e) => {
  e.preventDefault();
  const alertEl = $("#modal-share-alert");
  hideAlert(alertEl);

  const noteId = $("#share-note-id").value;
  const share_with_email = $("#share-email").value.trim();

  try {
    await api(`/notes/${noteId}/share`, {
      method: "POST",
      body: JSON.stringify({ share_with_email }),
    });
    showAlert(alertEl, "Note shared successfully!", "success");
    setTimeout(() => closeModal("modal-share"), 1200);
  } catch (err) {
    showAlert(alertEl, err.message);
  }
});

$$("[data-close]").forEach((btn) => {
  btn.addEventListener("click", () => closeModal(btn.dataset.close));
});

$$(".modal-overlay").forEach((overlay) => {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", toggleTheme);
  } else {
    console.warn("Theme toggle button not found in DOM");
  }

  const noteContent = $("#note-content");
  const noteTitle = $("#note-title");
  const hindiToggle = $("#hindi-toggle");
  const hindiHint = $("#hindi-hint");

  if (hindiToggle) {
    if (noteContent) noteContent.addEventListener("keyup", handleHindiInput);
    if (noteTitle) noteTitle.addEventListener("keyup", handleHindiInput);
    
    hindiToggle.addEventListener("change", () => {
      hindiHint?.classList.toggle("hidden", !hindiToggle.checked);
    });
  }

  handleOAuthCallback();
  if (getToken() && !new URLSearchParams(window.location.search).has("token")) {
    showAppView();
    loadNotes();
    return;
  }
  if (!getToken()) {
    showGuestView();
    loadAuthStatus();
  }
});
