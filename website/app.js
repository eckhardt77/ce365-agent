/**
 * CE365 Agent Website
 */

const API_URL = "https://license.ce365.de";

/* === Cookie Consent === */

function getCookieConsent() {
    return localStorage.getItem("ce365_consent");
}

function acceptCookies(level) {
    localStorage.setItem("ce365_consent", level);
    document.getElementById("cookie-banner").style.display = "none";

    if (level === "all") {
        loadGTM();
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({ event: "cookie_consent", consent_level: "all" });
    }
}

// Show banner if no consent yet
document.addEventListener("DOMContentLoaded", function () {
    const consent = getCookieConsent();
    if (!consent) {
        document.getElementById("cookie-banner").style.display = "block";
    } else if (consent === "all") {
        loadGTM();
    }
});

/* === Mobile Menu === */

function toggleMenu() {
    const nav = document.querySelector(".nav-links");
    nav.classList.toggle("open");
}

// Close mobile menu on link click
document.addEventListener("click", function (e) {
    if (e.target.closest(".nav-links a")) {
        document.querySelector(".nav-links").classList.remove("open");
    }
});

/* === Stripe Checkout === */

async function startCheckout(seats) {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.disabled = true;

    const lang = document.documentElement.lang === "en" ? "en" : "de";
    btn.textContent = lang === "en" ? "Loading..." : "Wird geladen...";

    try {
        const response = await fetch(`${API_URL}/api/stripe/create-checkout?seats=${seats}&lang=${lang}`, {
            method: "POST",
        });

        if (!response.ok) throw new Error("Checkout failed");

        const data = await response.json();
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            throw new Error("No checkout URL");
        }
    } catch (error) {
        alert(lang === "en"
            ? "Error starting checkout. Please try again."
            : "Fehler beim Starten des Checkouts. Bitte versuche es erneut.");
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

/* === Newsletter === */

async function submitNewsletter(e) {
    e.preventDefault();
    const form = e.target;
    const email = form.email.value.trim();
    const name = form.name.value.trim();
    const btn = form.querySelector("button");
    const successEl = document.getElementById("newsletter-success");
    const errorEl = document.getElementById("newsletter-error");

    successEl.style.display = "none";
    errorEl.style.display = "none";
    btn.textContent = "...";
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/api/newsletter/subscribe`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, name }),
        });
        if (!response.ok) throw new Error();
        successEl.style.display = "block";
        form.reset();
    } catch {
        errorEl.style.display = "block";
    } finally {
        btn.textContent = "Anmelden";
        btn.disabled = false;
    }
}

/* === Smooth Scroll === */

document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
        e.preventDefault();
        var target = document.querySelector(this.getAttribute("href"));
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
});
