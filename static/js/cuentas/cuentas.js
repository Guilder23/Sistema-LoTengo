document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form[data-bloquear-envio]").forEach((form) => {
        form.addEventListener("submit", () => {
            const button = form.querySelector('button[type="submit"]');
            if (!button) return;
            button.disabled = true;
            button.setAttribute("aria-busy", "true");
        });
    });
});
