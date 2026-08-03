const BOOT_TIMEOUT_MS = 120_000

let bootFailure = null
let bootComplete = false
let bootTimeout = null
let pyErrorObserver = null

function getElement(id) {
    return document.getElementById(id)
}

function formatError(error) {
    if (error instanceof Error) {
        return error.stack || error.message
    }

    if (typeof error === "string") {
        return error
    }

    try {
        return JSON.stringify(error) || String(error)
    } catch {
        return String(error)
    }
}

function renderFailure() {
    if (bootFailure === null || document.body === null) {
        return
    }

    const loader = getElement("loader")
    const title = getElement("loader-title")
    const status = getElement("status")
    const message = getElement("boot-error-message")
    const details = getElement("boot-error-details")

    if (loader === null || title === null || status === null || message === null || details === null) {
        return
    }

    loader.classList.remove("hide")
    loader.classList.add("boot-error")
    loader.setAttribute("role", "alert")
    loader.setAttribute("aria-live", "assertive")
    title.textContent = bootFailure.title
    status.textContent = "realkey could not start."
    message.textContent = bootFailure.message
    details.textContent = bootFailure.details

    const retry = getElement("boot-retry")
    retry?.addEventListener("click", () => window.location.reload(), { once: true })
}

function fail(title, message, details = "") {
    if (bootFailure !== null) {
        return
    }

    bootFailure = {
        title: String(title),
        message: String(message),
        details: formatError(details),
    }
    clearTimeout(bootTimeout)
    renderFailure()
}

function setStatus(message) {
    if (bootFailure !== null || bootComplete) {
        return
    }

    const status = getElement("status")
    if (status !== null) {
        status.textContent = String(message)
    }
}

function complete() {
    if (bootFailure !== null) {
        return
    }

    bootComplete = true
    clearTimeout(bootTimeout)
    pyErrorObserver?.disconnect()
    getElement("loader")?.classList.add("hide")
}

window.realkeyBoot = { complete, fail, setStatus }

window.addEventListener("error", (event) => {
    if (bootComplete || bootFailure !== null) {
        return
    }

    if (event.target instanceof HTMLScriptElement) {
        fail(
            "A required script could not be loaded",
            "Check your network connection and reload realkey.",
            event.target.src,
        )
        return
    }

    if (event instanceof ErrorEvent) {
        fail(
            "An error occurred while starting realkey",
            "Reload the page to try again. If the problem continues, review the technical details below.",
            event.error || `${event.message}\n${event.filename}:${event.lineno}:${event.colno}`,
        )
    }
}, true)

window.addEventListener("unhandledrejection", (event) => {
    if (!bootComplete && bootFailure === null) {
        fail(
            "A startup task failed",
            "Reload the page to try again. If the problem continues, review the technical details below.",
            event.reason,
        )
    }
})

window.addEventListener("py:ready", () => {
    setStatus("Python runtime ready. Starting interface...")
})

function detectPyScriptErrors() {
    const reportError = () => {
        if (bootComplete || bootFailure !== null) {
            return
        }

        const errorOutput = document.querySelector("py-error")
        const details = errorOutput?.textContent?.trim()
        if (details) {
            fail(
                "Python failed while starting realkey",
                "The Python application could not finish loading.",
                details,
            )
        }
    }

    reportError()
    pyErrorObserver = new MutationObserver(reportError)
    pyErrorObserver.observe(document.documentElement, {
        childList: true,
        characterData: true,
        subtree: true,
    })
}

document.addEventListener("DOMContentLoaded", () => {
    renderFailure()
    detectPyScriptErrors()
})

const missingFeatures = [
    ["WebAssembly", typeof WebAssembly !== "undefined"],
    ["Web Workers", typeof Worker !== "undefined"],
].filter(([, supported]) => !supported).map(([name]) => name)

if (missingFeatures.length > 0) {
    fail(
        "This browser cannot run realkey",
        "Update your browser or open realkey in a current browser.",
        `Missing required browser features: ${missingFeatures.join(", ")}`,
    )
} else {
    bootTimeout = setTimeout(() => {
        fail(
            "realkey took too long to start",
            "Check your network connection, then reload the page.",
            `Startup did not complete within ${BOOT_TIMEOUT_MS / 1000} seconds.`,
        )
    }, BOOT_TIMEOUT_MS)
}
