document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".cuenta-menu");
    const button = container?.querySelector(".cuenta-menu-boton");
    const menu = container?.querySelector(".cuenta-menu-panel");
    if (!container || !button || !menu) return;

    const setOpen = (open) => {
        button.setAttribute("aria-expanded", String(open));
        button.setAttribute("aria-label", open ? "Cerrar menú de cuenta" : "Abrir menú de cuenta");
        menu.hidden = !open;
    };

    button.addEventListener("click", () => {
        setOpen(button.getAttribute("aria-expanded") !== "true");
    });

    menu.addEventListener("click", (event) => {
        if (event.target.closest("a")) setOpen(false);
    });

    document.addEventListener("click", (event) => {
        if (!container.contains(event.target)) setOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && button.getAttribute("aria-expanded") === "true") {
            setOpen(false);
            button.focus();
        }
    });
});
