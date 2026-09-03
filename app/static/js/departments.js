const departmentTable = document.getElementById("departmentTable");
const departmentModal = document.getElementById("departmentModal");
const departmentForm = document.getElementById("departmentForm");
const departmentError = document.getElementById("departmentError");
const saveDepartmentButton = document.getElementById("saveDepartmentButton");

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

async function loadDepartments() {
    try {
        const departments = normalizeList(await apiRequest("/api/departments"));
        if (!departments.length) {
            departmentTable.innerHTML = '<tr><td colspan="4">No departments found.</td></tr>';
            return;
        }
        departmentTable.innerHTML = departments.map(department => `
            <tr>
                <td><strong>${escapeHtml(department.name)}</strong></td>
                <td>${escapeHtml(department.code)}</td>
                <td>${escapeHtml(department.head || "-")}</td>
                <td><span class="muted-text">Available</span></td>
            </tr>
        `).join("");
    } catch (error) {
        console.error(error);
        departmentTable.innerHTML = '<tr><td colspan="4">Failed to load departments.</td></tr>';
    }
}

function openDepartmentModal() {
    departmentForm.reset();
    departmentError.textContent = "";
    departmentModal.classList.remove("hidden");
    document.getElementById("departmentName").focus();
}

function closeDepartmentModal() {
    departmentModal.classList.add("hidden");
    departmentForm.reset();
    departmentError.textContent = "";
}

departmentForm.addEventListener("submit", async event => {
    event.preventDefault();
    departmentError.textContent = "";
    const payload = {
        name: document.getElementById("departmentName").value.trim(),
        code: document.getElementById("departmentCode").value.trim(),
        head: document.getElementById("departmentHead").value.trim()
    };

    saveDepartmentButton.disabled = true;
    saveDepartmentButton.textContent = "Creating...";
    try {
        await apiRequest("/api/departments", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        closeDepartmentModal();
        await loadDepartments();
    } catch (error) {
        departmentError.textContent = error.message;
    } finally {
        saveDepartmentButton.disabled = false;
        saveDepartmentButton.textContent = "Create Department";
    }
});

document.getElementById("newDepartmentButton").addEventListener("click", openDepartmentModal);
document.getElementById("closeDepartmentModal").addEventListener("click", closeDepartmentModal);
document.getElementById("cancelDepartmentButton").addEventListener("click", closeDepartmentModal);
departmentModal.addEventListener("click", event => {
    if (event.target === departmentModal) {
        closeDepartmentModal();
    }
});
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !departmentModal.classList.contains("hidden")) {
        closeDepartmentModal();
    }
});

document.getElementById("logoutButton").addEventListener("click", logoutAdmin);

loadDepartments();
