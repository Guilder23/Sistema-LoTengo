document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector(".footer-cuenta-arriba");
    if (!button) return;

    button.addEventListener("click", () => {
        const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
        window.scrollTo({ top: 0, behavior });
    });
});
