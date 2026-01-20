const toggleBtn = document.getElementById("toggle-edit");
const editor = document.getElementById("email-editor");

toggleBtn.addEventListener("click", () => {
    if (editor.hasAttribute("readonly")) {
        editor.removeAttribute("readonly");
        editor.focus();
        toggleBtn.innerText = "Lock";
        editor.style.borderColor = "#6366f1";
        editor.style.background = "#fff";
    } else {
        editor.setAttribute("readonly", true);
        toggleBtn.innerText = "Write!!";
        editor.style.borderColor = "#e2e8f0";
        editor.style.background = "#f8fafc";
    }
});

function validateEmailTemplate() {
    const text = document.getElementById("email-editor").value.trim();

    // Length check
    if (text.length < 20) {
        alert("Email body must be at least 20 characters long.");
        return false;
    }

    // REQUIRED placeholders
    const required = ["{name}", "{company}"];
    const missing = required.filter(tag => !text.includes(tag));

    if (missing.length > 0) {
        alert(
            "Missing required placeholder(s): " + missing.join(", ")
        );
        return false; // FORCE user to fix
    }

    // DISALLOW unknown placeholders
    const allowed = new Set(required);
    const matches = text.match(/{[^}]+}/g) || [];

    for (const m of matches) {
        if (!allowed.has(m)) {
            alert("Invalid placeholder detected: " + m);
            return false;
        }
    }

    return true;
}