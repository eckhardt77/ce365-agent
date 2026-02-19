/**
 * CE365 Agent Website
 */

const API_URL = "https://license.ce365.de";

/* === Cookie Consent (Granular) === */

function getCookieConsent() {
    var raw = localStorage.getItem("ce365_consent");
    if (!raw) return null;

    // Migration: old string format ("essential" / "all") -> new JSON format
    if (raw === "essential") {
        var migrated = { analytics: false, marketing: false };
        localStorage.setItem("ce365_consent", JSON.stringify(migrated));
        return migrated;
    }
    if (raw === "all") {
        var migrated = { analytics: true, marketing: true };
        localStorage.setItem("ce365_consent", JSON.stringify(migrated));
        return migrated;
    }

    try {
        return JSON.parse(raw);
    } catch (e) {
        localStorage.removeItem("ce365_consent");
        return null;
    }
}

function saveConsent(consent) {
    localStorage.setItem("ce365_consent", JSON.stringify(consent));
    document.getElementById("cookie-banner").style.display = "none";
    closeCookieSettings();
    applyConsent(consent);
}

function applyConsent(consent) {
    if (consent && consent.analytics) {
        loadGTM();
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({ event: "cookie_consent", consent_level: "analytics" });
    }
}

function acceptCookies(level) {
    if (level === "all") {
        saveConsent({ analytics: true, marketing: true });
    } else {
        saveConsent({ analytics: false, marketing: false });
    }
}

function openCookieSettings() {
    var modal = document.getElementById("cookie-modal");
    var consent = getCookieConsent();
    // Pre-fill toggles based on current consent
    var analyticsEl = document.getElementById("cookie-analytics");
    var marketingEl = document.getElementById("cookie-marketing");
    if (consent) {
        analyticsEl.checked = !!consent.analytics;
        marketingEl.checked = !!consent.marketing;
    } else {
        analyticsEl.checked = false;
        marketingEl.checked = false;
    }
    modal.style.display = "flex";
}

function closeCookieSettings() {
    document.getElementById("cookie-modal").style.display = "none";
}

function saveCookieSettings() {
    var analytics = document.getElementById("cookie-analytics").checked;
    var marketing = document.getElementById("cookie-marketing").checked;
    saveConsent({ analytics: analytics, marketing: marketing });
}

// Close modal on backdrop click
document.addEventListener("click", function (e) {
    var modal = document.getElementById("cookie-modal");
    if (e.target === modal) {
        closeCookieSettings();
    }
});

// Show banner if no consent yet, otherwise apply existing consent
document.addEventListener("DOMContentLoaded", function () {
    var consent = getCookieConsent();
    if (!consent) {
        document.getElementById("cookie-banner").style.display = "block";
    } else {
        applyConsent(consent);
    }
});

/* === Mobile Menu === */

function toggleMenu() {
    var nav = document.querySelector(".nav-links");
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
    var btn = event.target;
    var originalText = btn.textContent;
    btn.disabled = true;

    var lang = document.documentElement.lang === "en" ? "en" : "de";
    btn.textContent = lang === "en" ? "Loading..." : "Wird geladen...";

    try {
        var response = await fetch(API_URL + "/api/stripe/create-checkout?seats=" + seats + "&lang=" + lang, {
            method: "POST",
        });

        if (!response.ok) throw new Error("Checkout failed");

        var data = await response.json();
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
    var form = e.target;
    var email = form.email.value.trim();
    var name = form.name.value.trim();
    var btn = form.querySelector("button");
    var successEl = document.getElementById("newsletter-success");
    var errorEl = document.getElementById("newsletter-error");

    successEl.style.display = "none";
    errorEl.style.display = "none";
    btn.textContent = "...";
    btn.disabled = true;

    try {
        var response = await fetch(API_URL + "/api/newsletter/subscribe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, name: name }),
        });
        if (!response.ok) throw new Error();
        successEl.style.display = "block";
        form.reset();
    } catch (err) {
        errorEl.style.display = "block";
    } finally {
        var lang = document.documentElement.lang === "en" ? "en" : "de";
        btn.textContent = lang === "en" ? "Subscribe" : "Anmelden";
        btn.disabled = false;
    }
}

/* === Smooth Scroll === */

document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
        var href = this.getAttribute("href");
        if (href === "#") return; // skip cookie-settings link
        e.preventDefault();
        var target = document.querySelector(href);
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
});
