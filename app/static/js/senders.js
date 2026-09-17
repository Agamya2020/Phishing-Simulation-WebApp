const senderTable =
    document.getElementById("senderTable");

const senderModal =
    document.getElementById("senderModal");

const senderForm =
    document.getElementById("senderForm");

const senderError =
    document.getElementById("senderError");

const saveSenderButton =
    document.getElementById("saveSenderButton");


let resendSenders = [];
let gmailSenders = [];


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function normalizeList(data) {
    if (Array.isArray(data)) {
        return data;
    }

    if (data && Array.isArray(data.items)) {
        return data.items;
    }

    if (data && Array.isArray(data.data)) {
        return data.data;
    }

    return [];
}


async function loadSenders() {

    try {

        const [
            resendData,
            gmailData
        ] = await Promise.all([
            apiRequest("/api/senders"),
            apiRequest("/api/google/senders")
        ]);


        resendSenders =
            normalizeList(resendData);

        gmailSenders =
            normalizeList(gmailData);


        renderSenders();

    } catch (error) {

        console.error(error);

        senderTable.innerHTML = `
            <tr>
                <td colspan="7">
                    Failed to load sender identities.
                </td>
            </tr>
        `;
    }
}


function renderSenders() {

    const rows = [];


    // -------------------------------------------------
    // Resend senders
    // -------------------------------------------------

    resendSenders.forEach(sender => {

        rows.push(`
            <tr>

                <td>
                    <span class="status-badge">
                        Resend
                    </span>
                </td>

                <td>
                    <strong>
                        ${escapeHtml(sender.name)}
                    </strong>
                </td>

                <td>
                    ${escapeHtml(sender.email)}
                </td>

                <td>
                    ${escapeHtml(sender.domain)}
                </td>

                <td>
                    <span class="status-badge">
                        ${
                            sender.is_verified
                                ? "Verified"
                                : "Not Verified"
                        }
                    </span>
                </td>

                <td>
                    <span class="status-badge">
                        ${
                            sender.is_active
                                ? "Active"
                                : "Inactive"
                        }
                    </span>
                </td>

                <td>

                    <div class="action-buttons">

                        <button
                            class="table-action-button toggle-resend-button"
                            data-sender-id="${sender.id}"
                            type="button"
                        >
                            ${
                                sender.is_active
                                    ? "Disable"
                                    : "Enable"
                            }
                        </button>

                        <button
                            class="danger-button delete-resend-button"
                            data-sender-id="${sender.id}"
                            type="button"
                        >
                            Delete
                        </button>

                    </div>

                </td>

            </tr>
        `);
    });


    // -------------------------------------------------
    // Gmail senders
    // -------------------------------------------------

    gmailSenders.forEach(sender => {

        rows.push(`
            <tr>

                <td>
                    <span class="status-badge">
                        Gmail
                    </span>
                </td>

                <td>
                    <strong>
                        ${escapeHtml(
                            sender.display_name ||
                            sender.email
                        )}
                    </strong>
                </td>

                <td>
                    ${escapeHtml(sender.email)}
                </td>

                <td>
                    Google Account
                </td>

                <td>
                    <span class="status-badge">
                        OAuth Connected
                    </span>
                </td>

                <td>
                    <span class="status-badge">
                        ${
                            sender.is_active
                                ? "Active"
                                : "Inactive"
                        }
                    </span>
                </td>

                <td>

                    <div class="action-buttons">

                        <button
                            class="table-action-button toggle-gmail-button"
                            data-sender-id="${sender.id}"
                            type="button"
                        >
                            ${
                                sender.is_active
                                    ? "Disable"
                                    : "Enable"
                            }
                        </button>

                        <button
                            class="danger-button disconnect-gmail-button"
                            data-sender-id="${sender.id}"
                            type="button"
                        >
                            Disconnect
                        </button>

                    </div>

                </td>

            </tr>
        `);
    });


    if (!rows.length) {

        senderTable.innerHTML = `
            <tr>
                <td colspan="7">
                    No sender identities configured.
                </td>
            </tr>
        `;

        return;
    }


    senderTable.innerHTML =
        rows.join("");
}


function openSenderModal() {

    senderForm.reset();

    senderError.textContent = "";

    senderModal.classList.remove("hidden");

    document
        .getElementById("senderName")
        .focus();
}


function closeSenderModal() {

    senderModal.classList.add("hidden");

    senderForm.reset();

    senderError.textContent = "";
}


// -------------------------------------------------
// Create Resend sender
// -------------------------------------------------

senderForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        senderError.textContent = "";


        const payload = {

            name:
                document
                    .getElementById("senderName")
                    .value
                    .trim(),

            email:
                document
                    .getElementById("senderEmail")
                    .value
                    .trim()
        };


        saveSenderButton.disabled = true;
        saveSenderButton.textContent =
            "Adding...";


        try {

            await apiRequest(
                "/api/senders",
                {
                    method: "POST",
                    body: JSON.stringify(payload)
                }
            );


            closeSenderModal();

            await loadSenders();


        } catch (error) {

            senderError.textContent =
                error.message;

        } finally {

            saveSenderButton.disabled = false;
            saveSenderButton.textContent =
                "Add Sender";
        }
    }
);


// -------------------------------------------------
// Resend enable / disable
// -------------------------------------------------

async function toggleResend(senderId) {

    const sender =
        resendSenders.find(
            item =>
                String(item.id) ===
                String(senderId)
        );


    if (!sender) {
        return;
    }


    try {

        await apiRequest(
            `/api/senders/${encodeURIComponent(senderId)}`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    is_active:
                        !sender.is_active
                })
            }
        );


        await loadSenders();


    } catch (error) {

        window.alert(
            error.message
        );
    }
}


// -------------------------------------------------
// Gmail enable / disable
// -------------------------------------------------

async function toggleGmail(senderId) {

    const sender =
        gmailSenders.find(
            item =>
                String(item.id) ===
                String(senderId)
        );


    if (!sender) {
        return;
    }


    try {

        await apiRequest(
            `/api/google/senders/${encodeURIComponent(senderId)}`,
            {
                method: "PATCH",

                body: JSON.stringify({
                    is_active:
                        !sender.is_active
                })
            }
        );


        await loadSenders();


    } catch (error) {

        window.alert(
            error.message
        );
    }
}


// -------------------------------------------------
// Delete Resend
// -------------------------------------------------

async function deleteResend(senderId) {

    const sender =
        resendSenders.find(
            item =>
                String(item.id) ===
                String(senderId)
        );


    if (!sender) {
        return;
    }


    if (
        !window.confirm(
            `Delete sender "${sender.email}"?`
        )
    ) {
        return;
    }


    try {

        await apiRequest(
            `/api/senders/${encodeURIComponent(senderId)}`,
            {
                method: "DELETE"
            }
        );


        await loadSenders();


    } catch (error) {

        window.alert(
            error.message
        );
    }
}


// -------------------------------------------------
// Disconnect Gmail
// -------------------------------------------------

async function disconnectGmail(senderId) {

    const sender =
        gmailSenders.find(
            item =>
                String(item.id) ===
                String(senderId)
        );


    if (!sender) {
        return;
    }


    if (
        !window.confirm(
            `Disconnect Gmail account "${sender.email}" from PhishGuard?`
        )
    ) {
        return;
    }


    try {

        await apiRequest(
            `/api/google/senders/${encodeURIComponent(senderId)}`,
            {
                method: "DELETE"
            }
        );


        await loadSenders();


    } catch (error) {

        window.alert(
            error.message
        );
    }
}


// -------------------------------------------------
// Table actions
// -------------------------------------------------

senderTable.addEventListener(
    "click",
    event => {

        const resendToggle =
            event.target.closest(
                ".toggle-resend-button"
            );


        if (resendToggle) {

            toggleResend(
                resendToggle.dataset.senderId
            );

            return;
        }


        const gmailToggle =
            event.target.closest(
                ".toggle-gmail-button"
            );


        if (gmailToggle) {

            toggleGmail(
                gmailToggle.dataset.senderId
            );

            return;
        }


        const resendDelete =
            event.target.closest(
                ".delete-resend-button"
            );


        if (resendDelete) {

            deleteResend(
                resendDelete.dataset.senderId
            );

            return;
        }


        const gmailDisconnect =
            event.target.closest(
                ".disconnect-gmail-button"
            );


        if (gmailDisconnect) {

            disconnectGmail(
                gmailDisconnect.dataset.senderId
            );
        }
    }
);


// -------------------------------------------------
// Modal controls
// -------------------------------------------------

document
    .getElementById("newSenderButton")
    .addEventListener(
        "click",
        openSenderModal
    );


document
    .getElementById("closeSenderModal")
    .addEventListener(
        "click",
        closeSenderModal
    );


document
    .getElementById("cancelSenderButton")
    .addEventListener(
        "click",
        closeSenderModal
    );


senderModal.addEventListener(
    "click",
    event => {

        if (event.target === senderModal) {
            closeSenderModal();
        }
    }
);


document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape" &&
            !senderModal.classList.contains("hidden")
        ) {
            closeSenderModal();
        }
    }
);


document
    .getElementById("logoutButton")
    .addEventListener(
        "click",
        logoutAdmin
    );


// -------------------------------------------------
// Google OAuth result
// -------------------------------------------------

const params =
    new URLSearchParams(
        window.location.search
    );


if (
    params.get("gmail") ===
    "connected"
) {

    window.alert(
        "Gmail account connected successfully."
    );


    window.history.replaceState(
        {},
        "",
        "/admin/senders"
    );
}


loadSenders();
