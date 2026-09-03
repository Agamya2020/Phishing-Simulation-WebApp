const campaignId = document.body.dataset.campaignId;

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

function percentage(value, total) {
    return total ? `${((value / total) * 100).toFixed(1)}%` : "0%";
}

function formatDate(value) {
    if (!value) {
        return "-";
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

async function loadCampaign() {
    const encodedCampaignId = encodeURIComponent(campaignId);
    const [campaign, eventsData, usersData] = await Promise.all([
        apiRequest(`/api/campaigns/${encodedCampaignId}`),
        apiRequest(`/api/campaigns/${encodedCampaignId}/events`),
        apiRequest("/api/users")
    ]);

    const events = normalizeList(eventsData);
    const users = normalizeList(usersData);
    renderCampaign(campaign);
    renderRecipients(campaign, events, users);
    renderTimeline(events);
}

function renderCampaign(campaign) {
    document.getElementById("campaignName").textContent = campaign.name || "Campaign";
    document.getElementById("campaignDescription").textContent =
        campaign.description || "Phishing simulation campaign";
    document.getElementById("campaignStatus").textContent = campaign.status || "unknown";

    const targets = number(campaign.target_count);
    const opens = number(campaign.open_count);
    const clicks = number(campaign.click_count);
    const reports = number(campaign.report_count);
    const submissions = number(campaign.creds_count);

    document.getElementById("targetCount").textContent = targets;
    document.getElementById("openCount").textContent = opens;
    document.getElementById("clickCount").textContent = clicks;
    document.getElementById("reportCount").textContent = reports;
    document.getElementById("credsCount").textContent = submissions;
    document.getElementById("openRate").textContent = percentage(opens, targets);
    document.getElementById("clickRate").textContent = percentage(clicks, targets);
    document.getElementById("reportRate").textContent = percentage(reports, targets);
    document.getElementById("submissionRate").textContent = percentage(submissions, targets);
}

function renderRecipients(campaign, events, users) {
    const table = document.getElementById("recipientTable");
    const targetIds = Array.isArray(campaign.target_user_ids) ? campaign.target_user_ids : [];

    if (!targetIds.length) {
        table.innerHTML = '<tr><td colspan="7">No target users found.</td></tr>';
        return;
    }

    table.innerHTML = targetIds.map(userId => {
        const user = users.find(item => item.id === userId);
        const userEvents = events.filter(event => event.user_id === userId);
        const eventTypes = new Set(userEvents.map(event => event.event_type));
        return `
            <tr>
                <td><strong>${escapeHtml(user ? user.name : "Unknown User")}</strong></td>
                <td>${escapeHtml(user ? user.email : "-")}</td>
                <td>${statusIcon(eventTypes.has("sent"))}</td>
                <td>${statusIcon(eventTypes.has("opened"))}</td>
                <td>${statusIcon(eventTypes.has("clicked"))}</td>
                <td>${statusIcon(eventTypes.has("reported"))}</td>
                <td>${statusIcon(eventTypes.has("creds_entered"))}</td>
            </tr>
        `;
    }).join("");
}

function statusIcon(completed) {
    return completed
        ? '<span class="event-yes" aria-label="Yes">&#10003;</span>'
        : '<span class="event-no" aria-label="No">&mdash;</span>';
}

function renderTimeline(events) {
    const container = document.getElementById("eventTimeline");
    if (!events.length) {
        container.innerHTML = '<div class="timeline-empty">No campaign activity recorded.</div>';
        return;
    }

    container.innerHTML = events.map(event => `
        <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-title">${eventLabel(event.event_type)}</div>
                <div class="timeline-meta">
                    ${escapeHtml(event.user_email || "Unknown user")}
                    &middot;
                    ${escapeHtml(formatDate(event.timestamp))}
                </div>
            </div>
        </div>
    `).join("");
}

function eventLabel(eventType) {
    const labels = {
        sent: "Email sent",
        opened: "Email opened",
        clicked: "Simulation link clicked",
        reported: "Phishing message reported",
        creds_entered: "Simulation form submitted"
    };
    return labels[eventType] || escapeHtml(eventType);
}

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadCampaign().catch(error => {
    console.error(error);
    document.getElementById("campaignDescription").textContent = error.message;
    document.getElementById("recipientTable").innerHTML =
        '<tr><td colspan="7">Unable to load campaign analytics.</td></tr>';
    document.getElementById("eventTimeline").innerHTML =
        '<div class="timeline-empty">Unable to load campaign events.</div>';
});
