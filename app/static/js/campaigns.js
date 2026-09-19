const campaignTable = document.getElementById("campaignTable");
const modal = document.getElementById("campaignModal");
const campaignForm = document.getElementById("campaignForm");
const campaignError = document.getElementById("campaignError");
const createCampaignButton = document.getElementById("createCampaignButton");
const scheduleContainer = document.getElementById("scheduleContainer");
const scheduledAtInput = document.getElementById("scheduledAt");
let availableUsers = [];

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

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function number(value) {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? 0 : parsed;
}

async function loadCampaigns() {
    try {
        const campaigns = normalizeList(await apiRequest("/api/campaigns"));
        renderCampaigns(campaigns);
    } catch (error) {
        campaignTable.innerHTML = '<tr><td colspan="9">Failed to load campaigns.</td></tr>';
        console.error(error);
    }
}

function renderCampaigns(campaigns) {
    if (!campaigns.length) {
        campaignTable.innerHTML = '<tr><td colspan="9">No campaigns found.</td></tr>';
        return;
    }

    campaignTable.innerHTML = campaigns.map(campaign => {
        const canSend = campaign.status === "draft" || campaign.status === "scheduled";
        const detailUrl = `/admin/campaigns/${encodeURIComponent(campaign.id)}`;
        const detailHref = escapeHtml(detailUrl);
        const sendAction = canSend
            ? `<button class="table-action-button send-campaign-button" type="button"
                       data-campaign-id="${escapeHtml(campaign.id)}">Send</button>`
            : "";

        return `
            <tr>
                <td><a href="${detailHref}" class="campaign-link">${escapeHtml(campaign.name)}</a></td>
                <td><span class="status-badge">${escapeHtml(campaign.status || "unknown")}</span></td>
                <td>${formatScheduledTime(campaign.scheduled_at)}</td>
                <td>${number(campaign.target_count)}</td>
                <td>${number(campaign.open_count)}</td>
                <td>${number(campaign.click_count)}</td>
                <td>${number(campaign.report_count)}</td>
                <td>${number(campaign.creds_count)}</td>
                <td>
                    <div class="action-buttons">
                        <a href="${detailHref}" class="table-action-link">Details</a>
                        ${sendAction}
                        <button class="danger-button delete-campaign-button" type="button"
                                data-campaign-id="${escapeHtml(campaign.id)}">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function formatScheduledTime(value) {
    if (!value) {
        return "-";
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "-" : escapeHtml(date.toLocaleString());
}

async function loadFormData() {
    const [
        templatesData,
        usersData,
        groupsData,
        departmentsData,
        resendSendersData,
        gmailSendersData
    ] = await Promise.all([
        apiRequest("/api/templates"),
        apiRequest("/api/users"),
        apiRequest("/api/groups"),
        apiRequest("/api/departments"),
        apiRequest("/api/senders"),
        apiRequest("/api/google/senders")
    ]);

    availableUsers = normalizeList(usersData);

    renderTemplates(normalizeList(templatesData));
    renderUsers(availableUsers);
    renderTargetGroups(
        normalizeList(groupsData),
        normalizeList(departmentsData)
    );

    renderSenders(
        normalizeList(resendSendersData),
        normalizeList(gmailSendersData)
    );
}

function renderTemplates(templates) {
    const select = document.getElementById("templateSelect");
    select.innerHTML = '<option value="">Select template</option>';

    templates.forEach(template => {
        const option = document.createElement("option");
        option.value = template.id;
        option.textContent = template.name || template.subject || template.id;
        select.appendChild(option);
    });
}

function renderSenders(
    resendSenders,
    gmailSenders
) {
    const select =
        document.getElementById("senderSelect");

    select.innerHTML =
        '<option value="">Select sender</option>';


    const activeResendSenders =
        resendSenders.filter(
            sender =>
                sender.is_verified === true &&
                sender.is_active === true
        );


    const activeGmailSenders =
        gmailSenders.filter(
            sender =>
                sender.is_active === true
        );


    if (activeResendSenders.length) {

        const group =
            document.createElement("optgroup");

        group.label = "Resend";


        activeResendSenders.forEach(sender => {

            const option =
                document.createElement("option");

            option.value =
                `resend:${sender.id}`;

            option.textContent =
                `${sender.name} <${sender.email}>`;

            group.appendChild(option);
        });


        select.appendChild(group);
    }


    if (activeGmailSenders.length) {

        const group =
            document.createElement("optgroup");

        group.label = "Google / Gmail";


        activeGmailSenders.forEach(sender => {

            const option =
                document.createElement("option");

            option.value =
                `gmail:${sender.id}`;

            option.textContent =
                `${sender.display_name || sender.email} <${sender.email}>`;

            group.appendChild(option);
        });


        select.appendChild(group);
    }


    if (
        !activeResendSenders.length &&
        !activeGmailSenders.length
    ) {
        const option =
            document.createElement("option");

        option.value = "";
        option.disabled = true;

        option.textContent =
            "No active sender identities available";

        select.appendChild(option);
    }
}

function renderUsers(users) {
    const container = document.getElementById("userList");

    if (!users.length) {
        container.textContent = "No users available.";
        return;
    }

    container.innerHTML = users.map(user => `
        <label class="checkbox-item">
            <input type="checkbox" class="user-checkbox" value="${escapeHtml(user.id)}">
            <span>
                <strong>${escapeHtml(user.name)}</strong>
                <small>${escapeHtml(user.email)}</small>
            </span>
        </label>
    `).join("");
}

function renderTargetGroups(groups, departments) {
    const container = document.getElementById("groupList");

    if (!groups.length && !departments.length) {
        container.textContent = "No departments or groups available.";
        return;
    }

    let html = "";

    if (departments.length) {
        html += `
            <div class="selection-section">
                <strong>Departments</strong>
            </div>
        `;

        html += departments.map(department => `
            <label class="checkbox-item">
                <input
                    type="checkbox"
                    class="department-checkbox"
                    value="${escapeHtml(department.id)}"
                >
                <span>
                    <strong>${escapeHtml(department.name)}</strong>
                    <small>${escapeHtml(department.code || "")}</small>
                </span>
            </label>
        `).join("");
    }

    if (groups.length) {
        html += `
            <div class="selection-section" style="margin-top:16px;">
                <strong>Groups</strong>
            </div>
        `;

        html += groups.map(group => `
            <label class="checkbox-item">
                <input
                    type="checkbox"
                    class="group-checkbox"
                    value="${escapeHtml(group.id)}"
                >
                <span><strong>${escapeHtml(group.name)}</strong></span>
            </label>
        `).join("");
    }

    container.innerHTML = html;
}

document.getElementById("openCreateCampaign").addEventListener("click", async () => {
    const now = new Date();
    const localNow = new Date(now.getTime() - (now.getTimezoneOffset() * 60000));
    scheduledAtInput.min = localNow.toISOString().slice(0, 16);
    modal.classList.remove("hidden");
    campaignError.textContent = "";
    document.getElementById("campaignName").focus();

    try {
        await loadFormData();
    } catch (error) {
        campaignError.textContent = error.message;
    }
});

function closeModal() {
    modal.classList.add("hidden");
    campaignForm.reset();
    campaignError.textContent = "";
    scheduleContainer.classList.add("hidden");
    scheduledAtInput.required = false;
}

document.getElementById("closeCampaignModal").addEventListener("click", closeModal);
document.getElementById("cancelCampaign").addEventListener("click", closeModal);

modal.addEventListener("click", event => {
    if (event.target === modal) {
        closeModal();
    }
});

document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !modal.classList.contains("hidden")) {
        closeModal();
    }
});

document.querySelectorAll('input[name="deliveryMode"]').forEach(input => {
    input.addEventListener("change", event => {
        const scheduled = event.target.value === "scheduled";
        scheduleContainer.classList.toggle("hidden", !scheduled);
        scheduledAtInput.required = scheduled;
        if (!scheduled) {
            scheduledAtInput.value = "";
        }
    });
});

campaignForm.addEventListener("submit", async event => {
    event.preventDefault();
    campaignError.textContent = "";

    const name =
        document.getElementById("campaignName").value.trim();

    const templateId =
        document.getElementById("templateSelect").value;

    const senderSelection =
        document.getElementById("senderSelect").value;

    const directlySelectedUserIds = Array.from(
        document.querySelectorAll(".user-checkbox:checked")
    )
        .map(checkbox => checkbox.value);

    const departmentIds = Array.from(
        document.querySelectorAll(".department-checkbox:checked")
    )
        .map(checkbox => checkbox.value);

    const groupIds = Array.from(
        document.querySelectorAll(".group-checkbox:checked")
    )
        .map(checkbox => checkbox.value);

    const departmentUserIds = availableUsers
        .filter(user => departmentIds.includes(user.department_id))
        .map(user => user.id);

    const userIds = Array.from(new Set([
        ...directlySelectedUserIds,
        ...departmentUserIds
    ]));

    const deliveryMode = document.querySelector('input[name="deliveryMode"]:checked').value;

    if (!senderSelection) {
        campaignError.textContent =
            "Select a sender identity.";
        return;
    }

    const [
        senderProvider,
        senderIdValue
    ] = senderSelection.split(":");

    const senderId =
        Number(senderIdValue);

    if (
        !senderProvider ||
        !Number.isInteger(senderId)
    ) {
        campaignError.textContent =
            "Invalid sender selection.";
        return;
    }

    if (
        !userIds.length &&
        !groupIds.length
    ) {
        campaignError.textContent =
            "Select at least one department, group, or user.";
        return;
    }

    let scheduledAt = null;
    if (deliveryMode === "scheduled") {
        if (!scheduledAtInput.value) {
            campaignError.textContent = "Choose a date and time for the scheduled campaign.";
            return;
        }

        const localDate = new Date(scheduledAtInput.value);
        if (Number.isNaN(localDate.getTime()) || localDate <= new Date()) {
            campaignError.textContent = "Scheduled time must be in the future.";
            return;
        }
        scheduledAt = localDate.toISOString();
    }

    const payload = {
        name,
        description: "Security awareness simulation",
        vector: "email",
        template_id: templateId,

        sender_identity_id:
            senderProvider === "resend"
                ? senderId
                : null,

        gmail_sender_id:
            senderProvider === "gmail"
                ? senderId
                : null,

        target_user_ids: userIds,
        group_ids: groupIds,
        scheduled_at: scheduledAt,
        send_immediately: deliveryMode === "now"
    };

    createCampaignButton.disabled = true;
    createCampaignButton.textContent = "Creating...";

    try {
        await apiRequest("/api/campaigns", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        closeModal();
        await loadCampaigns();
    } catch (error) {
        campaignError.textContent = error.message;
    } finally {
        createCampaignButton.disabled = false;
        createCampaignButton.textContent = "Create Campaign";
    }
});

async function sendCampaign(campaignId) {
    if (!window.confirm("Send this phishing simulation campaign now?")) {
        return;
    }

    try {
        await apiRequest(`/api/campaigns/${encodeURIComponent(campaignId)}/send`, {method: "POST"});
        await loadCampaigns();
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteCampaign(campaignId) {
    if (!window.confirm("Delete this campaign and all of its tracking data?")) {
        return;
    }

    try {
        await apiRequest(`/api/campaigns/${encodeURIComponent(campaignId)}`, {
            method: "DELETE"
        });
        await loadCampaigns();
    } catch (error) {
        window.alert(error.message);
    }
}

campaignTable.addEventListener("click", event => {
    const sendButton = event.target.closest(".send-campaign-button");
    if (sendButton) {
        sendCampaign(sendButton.dataset.campaignId);
        return;
    }

    const deleteButton = event.target.closest(".delete-campaign-button");
    if (deleteButton) {
        deleteCampaign(deleteButton.dataset.campaignId);
    }
});

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadCampaigns();
