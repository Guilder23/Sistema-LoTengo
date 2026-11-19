document.addEventListener("DOMContentLoaded", () => {
    const contenedor = document.querySelector(".navbar-notificaciones");
    const boton = contenedor?.querySelector(".navbar-notificaciones-boton");
    const panel = contenedor?.querySelector(".navbar-notificaciones-panel");
    if (!contenedor || !boton || !panel) return;

    const cerrar = () => {
        boton.setAttribute("aria-expanded", "false");
        panel.hidden = true;
    };

    boton.addEventListener("click", () => {
        const abierto = boton.getAttribute("aria-expanded") === "true";
        boton.setAttribute("aria-expanded", String(!abierto));
        panel.hidden = abierto;
    });

    document.addEventListener("click", (evento) => {
        if (!contenedor.contains(evento.target)) cerrar();
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && boton.getAttribute("aria-expanded") === "true") {
            cerrar();
            boton.focus();
        }
    });
});
