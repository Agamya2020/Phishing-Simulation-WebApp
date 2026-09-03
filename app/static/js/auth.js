const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");
const loginButton = document.getElementById("loginButton");


async function checkExistingSession() {
    try {
        const response = await fetch("/api/auth/me", {
            credentials: "same-origin"
        });

        if (response.ok) {
            window.location.href = "/admin/dashboard";
        }
    } catch {
        // A network error leaves the login form available.
    }
}


loginForm.addEventListener("submit", async event => {
    event.preventDefault();
    loginError.textContent = "";
    loginButton.disabled = true;
    loginButton.textContent = "Signing in...";

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            credentials: "same-origin",
            body: JSON.stringify({username, password})
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.detail || "Login failed");
        }

        window.location.href = "/admin/dashboard";
    } catch (error) {
        loginError.textContent = error.message;
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Sign In";
    }
});


checkExistingSession();
