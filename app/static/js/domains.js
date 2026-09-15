const domainTable =
    document.getElementById("domainTable");

const domainModal =
    document.getElementById("domainModal");

const domainForm =
    document.getElementById("domainForm");

const domainError =
    document.getElementById("domainError");

const saveDomainButton =
    document.getElementById("saveDomainButton");

const dnsPanel =
    document.getElementById("dnsPanel");

const dnsRecords =
    document.getElementById("dnsRecords");

const dnsDomainName =
    document.getElementById("dnsDomainName");


let modalMode = "create";

let domains = [];


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function loadDomains() {

    try {

        domains = await apiRequest(
            "/api/domains"
        );

        renderDomains();

    } catch (error) {

        console.error(error);

        domainTable.innerHTML = `
            <tr>
                <td colspan="4">
                    Failed to load domains.
                </td>
            </tr>
        `;
    }
}


function renderDomains() {

    if (!domains.length) {

        domainTable.innerHTML = `
            <tr>
                <td colspan="4">
                    No sender domains configured.
                </td>
            </tr>
        `;

        return;
    }


    domainTable.innerHTML =
        domains.map(domain => {

            const verified =
                domain.status === "verified";


            return `
                <tr>

                    <td>
                        <strong>
                            ${escapeHtml(domain.domain)}
                        </strong>
                    </td>

                    <td>
                        <span class="status-badge">
                            ${escapeHtml(domain.status)}
                        </span>
                    </td>

                    <td>
                        ${escapeHtml(
                            domain.resend_domain_id || "-"
                        )}
                    </td>

                    <td>

                        <div class="action-buttons">

                            <button
                                type="button"
                                class="table-action-button view-domain-button"
                                data-domain-id="${domain.id}"
                            >
                                View DNS
                            </button>

                            ${
                                !verified
                                ? `
                                    <button
                                        type="button"
                                        class="table-action-button verify-domain-button"
                                        data-domain-id="${domain.id}"
                                    >
                                        Verify
                                    </button>
                                `
                                : ""
                            }

                        </div>

                    </td>

                </tr>
            `;

        }).join("");
}


function openModal(mode) {

    modalMode = mode;

    domainForm.reset();

    domainError.textContent = "";


    if (mode === "import") {

        document.getElementById(
            "domainModalTitle"
        ).textContent =
            "Import Existing Domain";

        document.getElementById(
            "domainModalDescription"
        ).textContent =
            "Link a domain that already exists in your Resend account.";

        saveDomainButton.textContent =
            "Import Domain";

    } else {

        document.getElementById(
            "domainModalTitle"
        ).textContent =
            "Add Domain";

        document.getElementById(
            "domainModalDescription"
        ).textContent =
            "Create a new sending domain in Resend.";

        saveDomainButton.textContent =
            "Add Domain";
    }


    domainModal.classList.remove(
        "hidden"
    );


    document.getElementById(
        "domainName"
    ).focus();
}


function closeModal() {

    domainModal.classList.add(
        "hidden"
    );

    domainForm.reset();

    domainError.textContent = "";
}


domainForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        domainError.textContent = "";


        const domain =
            document
                .getElementById("domainName")
                .value
                .trim();


        if (!domain) {
            return;
        }


        saveDomainButton.disabled = true;

        saveDomainButton.textContent =
            modalMode === "import"
                ? "Importing..."
                : "Adding...";


        try {

            let response;


            if (modalMode === "import") {

                response = await apiRequest(
                    "/api/domains/import",
                    {
                        method: "POST",
                        body: JSON.stringify({
                            domain
                        })
                    }
                );

            } else {

                response = await apiRequest(
                    "/api/domains",
                    {
                        method: "POST",
                        body: JSON.stringify({
                            domain
                        })
                    }
                );
            }


            closeModal();

            await loadDomains();


            if (response?.resend) {

                showDnsRecords(
                    response.domain,
                    response.resend
                );
            }


        } catch (error) {

            domainError.textContent =
                error.message;

        } finally {

            saveDomainButton.disabled = false;

            saveDomainButton.textContent =
                modalMode === "import"
                    ? "Import Domain"
                    : "Add Domain";
        }
    }
);


async function viewDomain(domainId) {

    try {

        const response =
            await apiRequest(
                `/api/domains/${encodeURIComponent(domainId)}`
            );


        showDnsRecords(
            response.domain,
            response.resend
        );


        await loadDomains();

    } catch (error) {

        window.alert(
            error.message
        );
    }
}


async function verifyDomain(domainId) {

    try {

        const response =
            await apiRequest(
                `/api/domains/${encodeURIComponent(domainId)}/verify`,
                {
                    method: "POST"
                }
            );


        showDnsRecords(
            response.domain,
            response.resend
        );


        await loadDomains();


        if (
            response.domain.status ===
            "verified"
        ) {

            window.alert(
                "Domain verified successfully."
            );

        } else {

            window.alert(
                `Current domain status: ${response.domain.status}`
            );
        }


    } catch (error) {

        window.alert(
            error.message
        );
    }
}


function showDnsRecords(
    localDomain,
    resendData
) {

    dnsPanel.classList.remove(
        "hidden"
    );


    dnsDomainName.textContent =
        localDomain.domain;


    const records =
        Array.isArray(resendData.records)
            ? resendData.records
            : [];


    if (!records.length) {

        dnsRecords.innerHTML = `
            <p>
                No DNS records were returned.
                The domain may already be verified.
            </p>
        `;

        return;
    }


    dnsRecords.innerHTML = `

        <table>

            <thead>
                <tr>
                    <th>Type</th>
                    <th>Name</th>
                    <th>Value</th>
                    <th>Status</th>
                </tr>
            </thead>

            <tbody>

                ${records.map(record => `

                    <tr>

                        <td>
                            ${escapeHtml(
                                record.record ||
                                record.type ||
                                "-"
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                record.name || "-"
                            )}
                        </td>

                        <td>
                            <code>
                                ${escapeHtml(
                                    record.value || "-"
                                )}
                            </code>
                        </td>

                        <td>
                            ${escapeHtml(
                                record.status || "-"
                            )}
                        </td>

                    </tr>

                `).join("")}

            </tbody>

        </table>
    `;


    dnsPanel.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


domainTable.addEventListener(
    "click",
    event => {

        const viewButton =
            event.target.closest(
                ".view-domain-button"
            );

        if (viewButton) {

            viewDomain(
                viewButton.dataset.domainId
            );

            return;
        }


        const verifyButton =
            event.target.closest(
                ".verify-domain-button"
            );

        if (verifyButton) {

            verifyDomain(
                verifyButton.dataset.domainId
            );
        }
    }
);


document
    .getElementById("addDomainButton")
    .addEventListener(
        "click",
        () => openModal("create")
    );


document
    .getElementById("importDomainButton")
    .addEventListener(
        "click",
        () => openModal("import")
    );


document
    .getElementById("closeDomainModal")
    .addEventListener(
        "click",
        closeModal
    );


document
    .getElementById("cancelDomainButton")
    .addEventListener(
        "click",
        closeModal
    );


domainModal.addEventListener(
    "click",
    event => {

        if (event.target === domainModal) {
            closeModal();
        }
    }
);


document
    .getElementById("logoutButton")
    .addEventListener(
        "click",
        logoutAdmin
    );


loadDomains();
