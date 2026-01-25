document.addEventListener("DOMContentLoaded", () => {
    initFilters();
    initKeyboardShortcuts();
    autoHideFlashMessage();
});

/* ---------------- GET CSRF TOKEN ---------------- */

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}

/* ---------------- FILTERS ---------------- */

function initFilters() {
    const filterButtons = document.querySelectorAll(".filter-btn[data-filter]");

    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const filter = btn.dataset.filter;

            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            document.querySelectorAll(".email-row").forEach(row => {
                const status = row.dataset.status;
                row.classList.toggle(
                    "hidden",
                    filter !== "all" && status !== filter
                );
            });
        });
    });
}

/* ---------------- KEYBOARD SHORTCUTS ---------------- */

function initKeyboardShortcuts() {
    document.addEventListener("keydown", e => {
        if (!e.altKey) return;

        const map = {
            "1": "all",
            "2": "SUCCESS",
            "3": "FAILED",
            "4": "PENDING"
        };

        if (map[e.key]) {
            document
                .querySelector(`.filter-btn[data-filter="${map[e.key]}"]`)
                ?.click();
        }
    });
}

/* ---------------- FLASH MESSAGE ---------------- */

function autoHideFlashMessage() {
    setTimeout(() => {
        const msg = document.querySelector(".flash-message");
        if (msg) msg.remove();
    }, 4000);
}

/* ---------------- DASHBOARD REFRESH ---------------- */

async function refreshDashboard() {
    const res = await fetch("/dashboard/data/");
    if (!res.ok) return;

    const { logs } = await res.json();
    const tbody = document.getElementById("email-table-body");

    logs.forEach(log => {
        let row = document.getElementById(`row-${log.id}`);

        if (!row) {
            row = createRow(log);
            tbody.prepend(row);
            highlight(row);
            return;
        }

        if (row.dataset.status !== log.status) {
            updateRowStatus(row, log.status);
            highlight(row);
        }
    });
}

setInterval(refreshDashboard, 15000);

/* ---------------- ROW HELPERS ---------------- */

function createRow(log) {
    const row = document.createElement("tr");
    row.className = "email-row";
    row.id = `row-${log.id}`;
    row.dataset.status = log.status;

    row.innerHTML = `
        <td>${log.email}</td>
        <td>${log.company}</td>
        <td>
            <span class="status-badge status-${log.status.toLowerCase()}">
                ${log.status}
            </span>
        </td>
        <td>${log.created_at}</td>
        <td>
            <button class="filter-btn view-details-btn" data-id="${log.id}">
                View Details
            </button>
            <div id="details-${log.id}" class="hidden"></div>
        </td>
    `;

    return row;
}

function updateRowStatus(row, status) {
    row.dataset.status = status;
    const badge = row.querySelector(".status-badge");
    badge.className = `status-badge status-${status.toLowerCase()}`;
    badge.textContent = status;
}

function highlight(el) {
    el.classList.add("row-highlight");
    setTimeout(() => el.classList.remove("row-highlight"), 1200);
}

/* ---------------- VIEW DETAILS (EVENT DELEGATION) ---------------- */

document.addEventListener("click", async e => {
    const btn = e.target.closest(".view-details-btn");
    if (!btn) return;

    const id = btn.dataset.id;
    toggleDetails(id);
});

document.addEventListener("click", e => {
    document.querySelectorAll(".details-dropdown").forEach(box => {
        if (!box.contains(e.target) &&
            !e.target.closest(".view-details-btn")) {
            box.classList.add("hidden");
            box.innerHTML = "";
        }
    });
});


async function toggleDetails(id) {
    const currentBox = document.getElementById(`details-${id}`);
    if (!currentBox) return;

    // CLOSE ALL OTHER DROPDOWNS
    document.querySelectorAll(".details-dropdown").forEach(box => {
        if (box !== currentBox) {
            box.classList.add("hidden");
            box.innerHTML = "";
        }
    });

    // TOGGLE CURRENT
    if (!currentBox.classList.contains("hidden")) {
        currentBox.classList.add("hidden");
        currentBox.innerHTML = "";
        return;
    }

    // OPEN CURRENT
    const res = await fetch(`/email/${id}/`);
    if (!res.ok) {
        currentBox.innerHTML = "Failed to load details";
        currentBox.classList.remove("hidden");
        return;
    }

    const data = await res.json();

    currentBox.innerHTML = `
        <p><b>Queued:</b> ${data.created_at}</p>
        <p><b>Sent:</b> ${data.sent_at ?? "Not sent yet"}</p>
        
        <hr style="margin:10px 0">

        <label><b>Schedule follow-up:</b></label>
        <select id="followup-days-${id}">
            <option value="3">3 days</option>
            <option value="7">7 days</option>
            <option value="14">14 days</option>
        </select>

        <button class="filter-btn"
                onclick="scheduleFollowUp(${id})"
                style="margin-top:8px;">
            Schedule
        </button>
        
        <hr style="margin:10px 0">

        <a href="${data.content_url}" target="_blank">
            View Email Content
        </a>
    `;
    if (data.status === "FAILED" && data.failure_reason) {
        currentBox.innerHTML += `
            <p style="color:#991b1b; margin-top:8px;">
                <b>Failure reason:</b> ${data.failure_reason}
            </p>
        `;
    }

    currentBox.classList.remove("hidden");
}

async function scheduleFollowUp(id) {
    const daysSelect = document.getElementById(`followup-days-${id}`);
    if (!daysSelect) return;

    const days = daysSelect.value;

    const res = await fetch(`/followup/${id}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ days }),
    });

    if (!res.ok) {
        alert("Failed to schedule follow-up");
        return;
    }

    daysSelect.innerHTML += `
        <p style="color:green; margin-top:6px;">
            Follow-up scheduled ✔
        </p>
    `;

    alert(`Follow-up scheduled in ${days} days`);
}
