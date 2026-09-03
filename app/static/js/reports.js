const exportCsvButton = document.getElementById("exportCsvButton");
let reportRows = [];

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
    return total ? (value / total) * 100 : 0;
}

function percentageText(value) {
    return `${value.toFixed(1)}%`;
}

function getDepartmentName(departmentId, departments) {
    const department = departments.find(item => item.id === departmentId);
    return department ? department.name : "Unassigned";
}

function calculateRisk(stats) {
    const score = (stats.clicks * 20) + (stats.submissions * 40) - (stats.reports * 20);
    return Math.max(0, Math.min(100, score));
}

function riskLevel(score) {
    if (score >= 70) {
        return "High";
    }
    if (score >= 40) {
        return "Medium";
    }
    return "Low";
}

async function loadCampaignEvents(campaigns) {
    const results = await Promise.all(campaigns.map(async campaign => {
        try {
            return normalizeList(await apiRequest(
                `/api/campaigns/${encodeURIComponent(campaign.id)}/events`
            ));
        } catch (error) {
            console.error("Failed to load campaign events:", campaign.id, error);
            return [];
        }
    }));
    return results.flat();
}

async function loadReports() {
    const [campaignsData, usersData, departmentsData] = await Promise.all([
        apiRequest("/api/campaigns"),
        apiRequest("/api/users"),
        apiRequest("/api/departments")
    ]);

    const campaigns = normalizeList(campaignsData);
    const users = normalizeList(usersData);
    const departments = normalizeList(departmentsData);
    const allEvents = await loadCampaignEvents(campaigns);

    renderSummary(campaigns);
    renderCampaignReport(campaigns);
    const userStats = buildUserStats(users, departments, allEvents);
    renderUserRisk(userStats);
    renderDepartmentReport(userStats, departments);
    reportRows = userStats;
    exportCsvButton.disabled = !reportRows.length;
}

function renderSummary(campaigns) {
    const totals = campaigns.reduce((result, campaign) => {
        result.targets += number(campaign.target_count);
        result.opens += number(campaign.open_count);
        result.clicks += number(campaign.click_count);
        result.reports += number(campaign.report_count);
        result.submissions += number(campaign.creds_count);
        return result;
    }, {targets: 0, opens: 0, clicks: 0, reports: 0, submissions: 0});

    document.getElementById("reportTargets").textContent = totals.targets;
    document.getElementById("reportOpenRate").textContent =
        percentageText(percentage(totals.opens, totals.targets));
    document.getElementById("reportClickRate").textContent =
        percentageText(percentage(totals.clicks, totals.targets));
    document.getElementById("reportReportRate").textContent =
        percentageText(percentage(totals.reports, totals.targets));
    document.getElementById("reportSubmissionRate").textContent =
        percentageText(percentage(totals.submissions, totals.targets));
}

function renderCampaignReport(campaigns) {
    const table = document.getElementById("campaignReportTable");
    if (!campaigns.length) {
        table.innerHTML = '<tr><td colspan="7">No campaigns available.</td></tr>';
        return;
    }

    table.innerHTML = campaigns.map(campaign => {
        const targets = number(campaign.target_count);
        const detailUrl = escapeHtml(`/admin/campaigns/${encodeURIComponent(campaign.id)}`);
        return `
            <tr>
                <td><a href="${detailUrl}" class="campaign-link">${escapeHtml(campaign.name)}</a></td>
                <td>${escapeHtml(campaign.status)}</td>
                <td>${targets}</td>
                <td>${percentageText(percentage(number(campaign.open_count), targets))}</td>
                <td>${percentageText(percentage(number(campaign.click_count), targets))}</td>
                <td>${percentageText(percentage(number(campaign.report_count), targets))}</td>
                <td>${percentageText(percentage(number(campaign.creds_count), targets))}</td>
            </tr>
        `;
    }).join("");
}

function buildUserStats(users, departments, events) {
    return users.map(user => {
        const stats = {
            user_id: user.id,
            name: user.name,
            email: user.email,
            department_id: user.department_id,
            department: getDepartmentName(user.department_id, departments),
            clicks: 0,
            reports: 0,
            submissions: 0,
            opens: 0
        };

        events.filter(event => event.user_id === user.id).forEach(event => {
            if (event.event_type === "clicked") {
                stats.clicks += 1;
            } else if (event.event_type === "reported") {
                stats.reports += 1;
            } else if (event.event_type === "creds_entered") {
                stats.submissions += 1;
            } else if (event.event_type === "opened") {
                stats.opens += 1;
            }
        });

        stats.risk_score = calculateRisk(stats);
        stats.risk_level = riskLevel(stats.risk_score);
        return stats;
    });
}

function renderUserRisk(users) {
    const table = document.getElementById("userRiskTable");
    if (!users.length) {
        table.innerHTML = '<tr><td colspan="8">No users available.</td></tr>';
        return;
    }

    const sorted = [...users].sort((a, b) => b.risk_score - a.risk_score);
    table.innerHTML = sorted.map(user => `
        <tr>
            <td><strong>${escapeHtml(user.name)}</strong></td>
            <td>${escapeHtml(user.email)}</td>
            <td>${escapeHtml(user.department)}</td>
            <td>${user.clicks}</td>
            <td>${user.reports}</td>
            <td>${user.submissions}</td>
            <td>${user.risk_score}</td>
            <td><span class="risk-badge risk-${user.risk_level.toLowerCase()}">
                ${user.risk_level}
            </span></td>
        </tr>
    `).join("");
}

function renderDepartmentReport(users, departments) {
    const table = document.getElementById("departmentReportTable");
    const rows = departments.map(department => {
        const departmentUsers = users.filter(user => user.department_id === department.id);
        const totals = departmentUsers.reduce((result, user) => {
            result.clicks += user.clicks;
            result.reports += user.reports;
            result.submissions += user.submissions;
            result.risk += user.risk_score;
            return result;
        }, {clicks: 0, reports: 0, submissions: 0, risk: 0});
        return {
            name: department.name,
            users: departmentUsers.length,
            clicks: totals.clicks,
            reports: totals.reports,
            submissions: totals.submissions,
            risk: departmentUsers.length ? totals.risk / departmentUsers.length : 0
        };
    });

    if (!rows.length) {
        table.innerHTML = '<tr><td colspan="6">No departments available.</td></tr>';
        return;
    }

    table.innerHTML = rows.map(row => `
        <tr>
            <td><strong>${escapeHtml(row.name)}</strong></td>
            <td>${row.users}</td>
            <td>${row.clicks}</td>
            <td>${row.reports}</td>
            <td>${row.submissions}</td>
            <td>${row.risk.toFixed(1)}</td>
        </tr>
    `).join("");
}

function csvCell(value) {
    let text = String(value ?? "");
    if (/^[\t\r ]*[=+\-@]/.test(text)) {
        text = `'${text}`;
    }
    return `"${text.replaceAll('"', '""')}"`;
}

function exportCsv() {
    if (!reportRows.length) {
        window.alert("No report data available.");
        return;
    }

    const headers = [
        "Name", "Email", "Department", "Clicks", "Reports",
        "Form Submissions", "Risk Score", "Risk Level"
    ];
    const rows = reportRows.map(user => [
        user.name, user.email, user.department, user.clicks, user.reports,
        user.submissions, user.risk_score, user.risk_level
    ]);
    const csv = [headers, ...rows].map(row => row.map(csvCell).join(",")).join("\r\n");
    const blob = new Blob(["\uFEFF", csv], {type: "text/csv;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "phishguard-awareness-report.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

function showReportError(error) {
    console.error("Reports failed:", error);
    document.getElementById("campaignReportTable").innerHTML =
        '<tr><td colspan="7">Failed to load campaign performance.</td></tr>';
    document.getElementById("userRiskTable").innerHTML =
        '<tr><td colspan="8">Failed to load risk data.</td></tr>';
    document.getElementById("departmentReportTable").innerHTML =
        '<tr><td colspan="6">Failed to load department performance.</td></tr>';
}

exportCsvButton.addEventListener("click", exportCsv);
document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadReports().catch(showReportError);
