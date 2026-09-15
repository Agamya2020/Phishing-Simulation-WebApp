const senderTable = document.getElementById("senderTable");

const senderModal = document.getElementById("senderModal");
const senderForm = document.getElementById("senderForm");

const senderError = document.getElementById("senderError");
const saveSenderButton = document.getElementById("saveSenderButton");

let loadedSenders = [];


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function loadSenders() {

    try {

        const data = await apiRequest("/api/senders");

        loadedSenders = Array.isArray(data)
            ? data
            : [];

        renderSenders();

    } catch (error) {

        console.error(error);

        senderTable.innerHTML = `
            <tr>
                <td colspan="6">
                    Failed to load sender identities.
                </td>
            </tr>
        `;
    }
}


function renderSenders() {

    if (!loadedSenders.length) {

        senderTable.innerHTML = `
            <tr>
                <td colspan="6">
                    No sender identities configured.
                </td>
            </tr>
        `;

        return;
    }


    senderTable.innerHTML = loadedSenders.map(sender => {

        const verification = sender.is_verified
            ? "Verified"
            : "Pending";

        const status = sender.is_active
            ? "Active"
            : "Inactive";


        return `
            <tr>

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
                        ${verification}
                    </span>
                </td>

                <td>
                    <span class="status-badge">
                        ${status}
                    </span>
                </td>

                <td>

                    <div class="action-buttons">

                        <button
                            class="table-action-button toggle-sender-button"
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
                            class="danger-button delete-sender-button"
                            data-sender-id="${sender.id}"
                            type="button"
                        >
                            Delete
                        </button>

                    </div>

                </td>

            </tr>
        `;

    }).join("");
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


async function updateSender(
    senderId,
    payload
) {

    try {

        await apiRequest(
            `/api/senders/${encodeURIComponent(senderId)}`,
            {
                method: "PATCH",
                body: JSON.stringify(payload)
            }
        );

        await loadSenders();

    } catch (error) {

        window.alert(error.message);
    }
}


async function deleteSender(senderId) {

    const sender =
        loadedSenders.find(
            item =>
                String(item.id) ===
                String(senderId)
        );


    if (!sender) {

        window.alert(
            "Sender identity not found."
        );

        return;
    }


    const confirmed =
        window.confirm(
            `Delete sender "${sender.email}"?`
        );


    if (!confirmed) {
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

        window.alert(error.message);
    }
}


senderTable.addEventListener(
    "click",
    async event => {

        const toggleButton =
            event.target.closest(
                ".toggle-sender-button"
            );


        if (toggleButton) {

            const sender =
                loadedSenders.find(
                    item =>
                        String(item.id) ===
                        String(toggleButton.dataset.senderId)
                );


            if (!sender) {
                return;
            }


            await updateSender(
                sender.id,
                {
                    is_active:
                        !sender.is_active
                }
            );

            return;
        }


        const deleteButton =
            event.target.closest(
                ".delete-sender-button"
            );


        if (deleteButton) {

            await deleteSender(
                deleteButton.dataset.senderId
            );
        }
    }
);


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


loadSenders();
