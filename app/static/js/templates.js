const templateTable = document.getElementById("templateTable");
const modal = document.getElementById("templateModal");
const templateForm = document.getElementById("templateForm");
const templateError = document.getElementById("templateError");
const saveTemplateButton = document.getElementById("saveTemplateButton");
let loadedTemplates = [];

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

async function loadTemplates() {
    try {
        renderTemplates(normalizeList(await apiRequest("/api/templates")));
    } catch (error) {
        console.error(error);
        templateTable.innerHTML = '<tr><td colspan="7">Failed to load templates.</td></tr>';
    }
}

function renderTemplates(templates) {
    loadedTemplates = templates;

    if (!templates.length) {
        templateTable.innerHTML = '<tr><td colspan="7">No templates found.</td></tr>';
        return;
    }

    templateTable.innerHTML = templates.map(template => `
        <tr>
            <td><strong>${escapeHtml(template.name)}</strong></td>
            <td>${escapeHtml(template.category)}</td>
            <td>${escapeHtml(template.vector)}</td>
            <td>${escapeHtml(template.subject)}</td>
            <td>${escapeHtml(template.sender)}</td>
            <td>${Number(template.uses) || 0}</td>
            <td>
                <div class="action-buttons">
                    <button
                        class="table-action-button edit-template-button"
                        type="button"
                        data-template-id="${escapeHtml(template.id)}"
                    >Edit</button>
                    <button
                        class="danger-button delete-template-button"
                        type="button"
                        data-template-id="${escapeHtml(template.id)}"
                    >Delete</button>
                </div>
            </td>
        </tr>
    `).join("");
}

function openCreateTemplate() {
    templateForm.reset();
    document.getElementById("templateId").value = "";
    document.getElementById("templateModalTitle").textContent = "Create Template";
    saveTemplateButton.textContent = "Save Template";
    templateError.textContent = "";
    updatePreview();
    modal.classList.remove("hidden");
    document.getElementById("templateName").focus();
}

function ensureSelectValue(select, value) {
    if (value && !Array.from(select.options).some(option => option.value === value)) {
        select.add(new Option(value, value));
    }
    select.value = value || "";
}

function editTemplate(template) {
    document.getElementById("templateId").value = template.id;
    document.getElementById("templateName").value = template.name || "";
    ensureSelectValue(document.getElementById("templateCategory"), template.category);
    ensureSelectValue(document.getElementById("templateVector"), template.vector);
    document.getElementById("templateSender").value = template.sender || "";
    document.getElementById("templateSubject").value = template.subject || "";
    document.getElementById("templateBody").value = template.body || "";
    document.getElementById("templateModalTitle").textContent = "Edit Template";
    saveTemplateButton.textContent = "Update Template";
    templateError.textContent = "";
    updatePreview();
    modal.classList.remove("hidden");
    document.getElementById("templateName").focus();
}

function editTemplateById(templateId) {
    const template = loadedTemplates.find(item => item.id === templateId);
    if (!template) {
        window.alert("Template not found.");
        return;
    }
    editTemplate(template);
}

function closeTemplateModal() {
    modal.classList.add("hidden");
    templateForm.reset();
    templateError.textContent = "";
}

function updatePreview() {
    const sender = document.getElementById("templateSender").value;
    const subject = document.getElementById("templateSubject").value;
    const body = document.getElementById("templateBody").value;

    document.getElementById("previewSender").textContent = sender || "-";
    document.getElementById("previewSubject").textContent = subject || "-";
    document.getElementById("previewBody").textContent =
        body || "Email preview will appear here.";
}

templateForm.addEventListener("submit", async event => {
    event.preventDefault();
    templateError.textContent = "";

    const templateId = document.getElementById("templateId").value;
    const payload = {
        name: document.getElementById("templateName").value.trim(),
        category: document.getElementById("templateCategory").value,
        vector: document.getElementById("templateVector").value,
        sender: document.getElementById("templateSender").value.trim(),
        subject: document.getElementById("templateSubject").value.trim(),
        body: document.getElementById("templateBody").value
    };

    saveTemplateButton.disabled = true;
    saveTemplateButton.textContent = templateId ? "Updating..." : "Saving...";

    try {
        await apiRequest(
            templateId ? `/api/templates/${encodeURIComponent(templateId)}` : "/api/templates",
            {
                method: templateId ? "PATCH" : "POST",
                body: JSON.stringify(payload)
            }
        );
        closeTemplateModal();
        await loadTemplates();
    } catch (error) {
        templateError.textContent = error.message;
    } finally {
        saveTemplateButton.disabled = false;
        saveTemplateButton.textContent = templateId ? "Update Template" : "Save Template";
    }
});

async function deleteTemplate(templateId) {
    if (!window.confirm("Delete this template?")) {
        return;
    }

    try {
        await apiRequest(`/api/templates/${encodeURIComponent(templateId)}`, {method: "DELETE"});
        await loadTemplates();
    } catch (error) {
        window.alert(error.message);
    }
}

templateTable.addEventListener("click", event => {
    const editButton = event.target.closest(".edit-template-button");
    if (editButton) {
        editTemplateById(editButton.dataset.templateId);
        return;
    }

    const deleteButton = event.target.closest(".delete-template-button");
    if (deleteButton) {
        deleteTemplate(deleteButton.dataset.templateId);
    }
});

document.getElementById("newTemplateButton").addEventListener("click", openCreateTemplate);
document.getElementById("closeTemplateModal").addEventListener("click", closeTemplateModal);
document.getElementById("cancelTemplateButton").addEventListener("click", closeTemplateModal);

modal.addEventListener("click", event => {
    if (event.target === modal) {
        closeTemplateModal();
    }
});

document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !modal.classList.contains("hidden")) {
        closeTemplateModal();
    }
});

["templateSender", "templateSubject", "templateBody"].forEach(id => {
    document.getElementById(id).addEventListener("input", updatePreview);
});

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadTemplates();
