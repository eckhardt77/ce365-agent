/**
 * CE365 Agent Website — Frontend Logic
 */

const API_URL = "https://license.ce365.de";

/**
 * Stripe Checkout starten
 */
async function startCheckout(seats) {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = "Wird geladen...";
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/api/stripe/create-checkout?seats=${seats}`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Checkout konnte nicht erstellt werden");
        }

        const data = await response.json();

        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            throw new Error("Keine Checkout-URL erhalten");
        }
    } catch (error) {
        console.error("Checkout Error:", error);
        alert("Fehler beim Starten des Checkouts. Bitte versuche es später erneut.");
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

/**
 * Smooth Scroll für Anchor-Links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
});

/**
 * Nav Background on scroll
 */
window.addEventListener("scroll", () => {
    const nav = document.querySelector(".nav");
    if (window.scrollY > 20) {
        nav.style.borderBottomColor = "rgba(51, 65, 85, 0.8)";
    } else {
        nav.style.borderBottomColor = "rgba(51, 65, 85, 0.3)";
    }
});
