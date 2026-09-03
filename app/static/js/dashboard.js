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

function number(value) {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? 0 : parsed;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function loadDashboard() {
    try {
        const [usersData, groupsData, templatesData, campaignsData] = await Promise.all([
            apiRequest("/api/users"),
            apiRequest("/api/groups"),
            apiRequest("/api/templates"),
            apiRequest("/api/campaigns")
        ]);

        const users = normalizeList(usersData);
        const groups = normalizeList(groupsData);
        const templates = normalizeList(templatesData);
        const campaigns = normalizeList(campaignsData);

        document.getElementById("totalUsers").textContent = users.length;
        document.getElementById("totalGroups").textContent = groups.length;
        document.getElementById("totalTemplates").textContent = templates.length;
        document.getElementById("totalCampaigns").textContent = campaigns.length;

        let targetCount = 0;
        let openCount = 0;
        let clickCount = 0;
        let reportCount = 0;
        let credsCount = 0;

        campaigns.forEach(campaign => {
            targetCount += number(campaign.target_count);
            openCount += number(campaign.open_count);
            clickCount += number(campaign.click_count);
            reportCount += number(campaign.report_count);
            credsCount += number(campaign.creds_count);
        });

        document.getElementById("targetCount").textContent = targetCount;
        document.getElementById("openCount").textContent = openCount;
        document.getElementById("clickCount").textContent = clickCount;
        document.getElementById("reportCount").textContent = reportCount;
        document.getElementById("credsCount").textContent = credsCount;

        renderCampaigns(campaigns);
    } catch (error) {
        console.error("Dashboard error:", error);
    }
}

function renderCampaigns(campaigns) {
    const table = document.getElementById("campaignTable");

    if (!campaigns.length) {
        table.innerHTML = '<tr><td colspan="7">No campaigns found.</td></tr>';
        return;
    }

    table.innerHTML = campaigns.slice(0, 10).map(campaign => `
        <tr>
            <td><strong>${escapeHtml(campaign.name)}</strong></td>
            <td><span class="status-badge">${escapeHtml(campaign.status || "unknown")}</span></td>
            <td>${number(campaign.target_count)}</td>
            <td>${number(campaign.open_count)}</td>
            <td>${number(campaign.click_count)}</td>
            <td>${number(campaign.report_count)}</td>
            <td>${number(campaign.creds_count)}</td>
        </tr>
    `).join("");
}

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadDashboard();
