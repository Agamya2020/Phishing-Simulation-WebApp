const campaignTable = document.getElementById("campaignTable");
const modal = document.getElementById("campaignModal");
const campaignForm = document.getElementById("campaignForm");
const campaignError = document.getElementById("campaignError");
const createCampaignButton = document.getElementById("createCampaignButton");
const scheduleContainer = document.getElementById("scheduleContainer");
const scheduledAtInput = document.getElementById("scheduledAt");

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
    const [templatesData, usersData, groupsData] = await Promise.all([
        apiRequest("/api/templates"),
        apiRequest("/api/users"),
        apiRequest("/api/groups")
    ]);

    renderTemplates(normalizeList(templatesData));
    renderUsers(normalizeList(usersData));
    renderGroups(normalizeList(groupsData));
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

function renderGroups(groups) {
    const container = document.getElementById("groupList");

    if (!groups.length) {
        container.textContent = "No groups available.";
        return;
    }

    container.innerHTML = groups.map(group => `
        <label class="checkbox-item">
            <input type="checkbox" class="group-checkbox" value="${escapeHtml(group.id)}">
            <span><strong>${escapeHtml(group.name)}</strong></span>
        </label>
    `).join("");
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

    const name = document.getElementById("campaignName").value.trim();
    const templateId = document.getElementById("templateSelect").value;
    const userIds = Array.from(document.querySelectorAll(".user-checkbox:checked"))
        .map(checkbox => checkbox.value);
    const groupIds = Array.from(document.querySelectorAll(".group-checkbox:checked"))
        .map(checkbox => checkbox.value);
    const deliveryMode = document.querySelector('input[name="deliveryMode"]:checked').value;

    if (!userIds.length && !groupIds.length) {
        campaignError.textContent = "Select at least one user or group.";
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

campaignTable.addEventListener("click", event => {
    const button = event.target.closest(".send-campaign-button");
    if (button) {
        sendCampaign(button.dataset.campaignId);
    }
});

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadCampaigns();
