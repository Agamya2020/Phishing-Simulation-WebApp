const groupTable = document.getElementById("groupTable");
const groupModal = document.getElementById("groupModal");
const groupForm = document.getElementById("groupForm");
const groupError = document.getElementById("groupError");
const saveGroupButton = document.getElementById("saveGroupButton");
let users = [];
let departments = [];

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

function getDepartmentName(id) {
    const department = departments.find(item => item.id === id);
    return department ? department.name : "-";
}

async function loadData() {
    try {
        const [groupData, userData, departmentData] = await Promise.all([
            apiRequest("/api/groups"),
            apiRequest("/api/users"),
            apiRequest("/api/departments")
        ]);
        users = normalizeList(userData);
        departments = normalizeList(departmentData);
        renderGroups(normalizeList(groupData));
        renderUsers();
        renderDepartments();
    } catch (error) {
        console.error(error);
        groupTable.innerHTML = '<tr><td colspan="3">Failed to load groups.</td></tr>';
    }
}

function renderGroups(groups) {
    if (!groups.length) {
        groupTable.innerHTML = '<tr><td colspan="3">No groups found.</td></tr>';
        return;
    }
    groupTable.innerHTML = groups.map(group => `
        <tr>
            <td><strong>${escapeHtml(group.name)}</strong></td>
            <td>${escapeHtml(getDepartmentName(group.department_id))}</td>
            <td>${Array.isArray(group.member_ids) ? group.member_ids.length : 0}</td>
        </tr>
    `).join("");
}

function renderUsers() {
    const container = document.getElementById("groupUserList");
    if (!users.length) {
        container.textContent = "No users available.";
        return;
    }
    container.innerHTML = users.map(user => `
        <label class="checkbox-item">
            <input type="checkbox" class="group-user-checkbox" value="${escapeHtml(user.id)}">
            <span>
                <strong>${escapeHtml(user.name)}</strong>
                <small>${escapeHtml(user.email)}</small>
            </span>
        </label>
    `).join("");
}

function renderDepartments() {
    const select = document.getElementById("groupDepartment");
    select.innerHTML = '<option value="">No department</option>';
    departments.forEach(department => {
        const option = document.createElement("option");
        option.value = department.id;
        option.textContent = department.name;
        select.appendChild(option);
    });
}

function openGroupModal() {
    groupForm.reset();
    groupError.textContent = "";
    groupModal.classList.remove("hidden");
    document.getElementById("groupName").focus();
}

function closeGroupModal() {
    groupModal.classList.add("hidden");
    groupForm.reset();
    groupError.textContent = "";
}

groupForm.addEventListener("submit", async event => {
    event.preventDefault();
    groupError.textContent = "";
    const memberIds = Array.from(document.querySelectorAll(".group-user-checkbox:checked"))
        .map(checkbox => checkbox.value);
    const payload = {
        name: document.getElementById("groupName").value.trim(),
        department_id: document.getElementById("groupDepartment").value || null,
        member_ids: memberIds
    };

    saveGroupButton.disabled = true;
    saveGroupButton.textContent = "Creating...";
    try {
        await apiRequest("/api/groups", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        closeGroupModal();
        await loadData();
    } catch (error) {
        groupError.textContent = error.message;
    } finally {
        saveGroupButton.disabled = false;
        saveGroupButton.textContent = "Create Group";
    }
});

document.getElementById("newGroupButton").addEventListener("click", openGroupModal);
document.getElementById("closeGroupModal").addEventListener("click", closeGroupModal);
document.getElementById("cancelGroupButton").addEventListener("click", closeGroupModal);
groupModal.addEventListener("click", event => {
    if (event.target === groupModal) {
        closeGroupModal();
    }
});
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !groupModal.classList.contains("hidden")) {
        closeGroupModal();
    }
});

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadData();
