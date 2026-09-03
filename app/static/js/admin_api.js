function getCookie(name) {
    const cookies = document.cookie.split(";");

    for (const cookie of cookies) {
        const [key, ...valueParts] = cookie.trim().split("=");
        if (key === name) {
            return decodeURIComponent(valueParts.join("="));
        }
    }

    return null;
}


async function apiRequest(url, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = {...options.headers};

    if (options.body && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
        const csrfToken = getCookie("phishguard_csrf");
        if (csrfToken) {
            headers["X-CSRF-Token"] = csrfToken;
        }
    }

    const response = await fetch(url, {
        ...options,
        method,
        headers,
        credentials: "same-origin"
    });

    if (response.status === 401) {
        window.location.href = "/admin/login";
        throw new Error("Your session has expired.");
    }

    if (response.status === 403) {
        let message = "Access denied.";
        try {
            const data = await response.json();
            message = data.detail || message;
        } catch {
            // The server did not return a JSON error response.
        }
        throw new Error(message);
    }

    if (!response.ok) {
        let message = "Request failed";
        try {
            const data = await response.json();
            message = data.detail || message;
        } catch {
            // The server did not return a JSON error response.
        }
        throw new Error(message);
    }

    if (response.status === 204) {
        return null;
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        return response.json();
    }

    return response.text();
}


async function logoutAdmin() {
    try {
        await apiRequest("/api/auth/logout", {method: "POST"});
    } catch (error) {
        console.error("Logout failed:", error);
    }

    window.location.href = "/admin/login";
}
