const userTable = document.getElementById("userTable");
const userModal = document.getElementById("userModal");
const userForm = document.getElementById("userForm");
const userError = document.getElementById("userError");
const saveUserButton = document.getElementById("saveUserButton");
let loadedUsers = [];
let loadedDepartments = [];

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

function departmentName(departmentId) {
    const department = loadedDepartments.find(item => item.id === departmentId);
    return department ? department.name : "-";
}

async function loadUsers() {
    try {
        const [usersData, departmentsData] = await Promise.all([
            apiRequest("/api/users"),
            apiRequest("/api/departments")
        ]);
        loadedUsers = normalizeList(usersData);
        loadedDepartments = normalizeList(departmentsData);
        renderUsers();
        renderDepartmentOptions();
    } catch (error) {
        console.error(error);
        userTable.innerHTML = '<tr><td colspan="7">Failed to load users.</td></tr>';
    }
}

function renderUsers() {
    if (!loadedUsers.length) {
        userTable.innerHTML = '<tr><td colspan="7">No users found.</td></tr>';
        return;
    }

    userTable.innerHTML = loadedUsers.map(user => `
        <tr>
            <td><strong>${escapeHtml(user.name)}</strong></td>
            <td>${escapeHtml(user.email)}</td>
            <td>${escapeHtml(user.role)}</td>
            <td>${escapeHtml(departmentName(user.department_id))}</td>
            <td><span class="status-badge">${escapeHtml(user.status)}</span></td>
            <td>${Number(user.risk_score) || 0}</td>
            <td>
                <div class="action-buttons">
                    <button class="table-action-button edit-user-button" type="button"
                            data-user-id="${escapeHtml(user.id)}">Edit</button>
                    <button class="danger-button delete-user-button" type="button"
                            data-user-id="${escapeHtml(user.id)}">Delete</button>
                </div>
            </td>
        </tr>
    `).join("");
}

function renderDepartmentOptions() {
    const select = document.getElementById("userDepartment");
    select.innerHTML = '<option value="">No department</option>';
    loadedDepartments.forEach(department => {
        const option = document.createElement("option");
        option.value = department.id;
        option.textContent = department.name;
        select.appendChild(option);
    });
}

function openUserModal() {
    userForm.reset();
    document.getElementById("userId").value = "";
    document.getElementById("userModalTitle").textContent = "Add User";
    saveUserButton.textContent = "Save User";
    userError.textContent = "";
    userModal.classList.remove("hidden");
    document.getElementById("userName").focus();
}

function editUser(userId) {
    const user = loadedUsers.find(item => item.id === userId);
    if (!user) {
        window.alert("User not found.");
        return;
    }

    document.getElementById("userId").value = user.id;
    document.getElementById("userName").value = user.name || "";
    document.getElementById("userEmail").value = user.email || "";
    document.getElementById("userRole").value = user.role || "";
    document.getElementById("userStatus").value = user.status || "active";
    document.getElementById("userDepartment").value = user.department_id || "";
    document.getElementById("userModalTitle").textContent = "Edit User";
    saveUserButton.textContent = "Update User";
    userError.textContent = "";
    userModal.classList.remove("hidden");
    document.getElementById("userName").focus();
}

function closeUserModal() {
    userModal.classList.add("hidden");
    userForm.reset();
    userError.textContent = "";
}

userForm.addEventListener("submit", async event => {
    event.preventDefault();
    userError.textContent = "";
    const userId = document.getElementById("userId").value;
    const payload = {
        name: document.getElementById("userName").value.trim(),
        email: document.getElementById("userEmail").value.trim(),
        role: document.getElementById("userRole").value.trim(),
        status: document.getElementById("userStatus").value,
        department_id: document.getElementById("userDepartment").value || null
    };

    saveUserButton.disabled = true;
    saveUserButton.textContent = userId ? "Updating..." : "Saving...";
    try {
        await apiRequest(userId ? `/api/users/${encodeURIComponent(userId)}` : "/api/users", {
            method: userId ? "PATCH" : "POST",
            body: JSON.stringify(payload)
        });
        closeUserModal();
        await loadUsers();
    } catch (error) {
        userError.textContent = error.message;
    } finally {
        saveUserButton.disabled = false;
        saveUserButton.textContent = userId ? "Update User" : "Save User";
    }
});

async function deleteUser(userId) {
    if (!window.confirm("Delete this user?")) {
        return;
    }
    try {
        await apiRequest(`/api/users/${encodeURIComponent(userId)}`, {method: "DELETE"});
        await loadUsers();
    } catch (error) {
        window.alert(error.message);
    }
}

userTable.addEventListener("click", event => {
    const editButton = event.target.closest(".edit-user-button");
    if (editButton) {
        editUser(editButton.dataset.userId);
        return;
    }
    const deleteButton = event.target.closest(".delete-user-button");
    if (deleteButton) {
        deleteUser(deleteButton.dataset.userId);
    }
});

document.getElementById("newUserButton").addEventListener("click", openUserModal);
document.getElementById("closeUserModal").addEventListener("click", closeUserModal);
document.getElementById("cancelUserButton").addEventListener("click", closeUserModal);
userModal.addEventListener("click", event => {
    if (event.target === userModal) {
        closeUserModal();
    }
});
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !userModal.classList.contains("hidden")) {
        closeUserModal();
    }
});

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadUsers();
