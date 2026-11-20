document.addEventListener("DOMContentLoaded", () => {
    const notificaciones = document.querySelector(".navbar-notificaciones");
    const botonNotificaciones = notificaciones?.querySelector(".navbar-notificaciones-boton");
    const panelNotificaciones = notificaciones?.querySelector(".navbar-notificaciones-panel");
    const menuCuenta = document.querySelector(".navbar-cuenta-menu");
    const botonCuenta = menuCuenta?.querySelector("[data-navbar-cuenta-boton]");
    const panelCuenta = menuCuenta?.querySelector(".navbar-cuenta-panel");
    const navegacion = document.getElementById("navegacionPrincipal");

    const cerrarNotificaciones = () => {
        botonNotificaciones?.setAttribute("aria-expanded", "false");
        if (panelNotificaciones) panelNotificaciones.hidden = true;
    };

    const cerrarCuenta = () => {
        botonCuenta?.setAttribute("aria-expanded", "false");
        if (panelCuenta) panelCuenta.hidden = true;
    };

    const cerrarNavegacionMovil = () => {
        if (
            navegacion?.classList.contains("show")
            && window.innerWidth < 992
            && window.bootstrap
        ) {
            window.bootstrap.Collapse.getOrCreateInstance(navegacion).hide();
        }
    };

    botonNotificaciones?.addEventListener("click", () => {
        const abierto = botonNotificaciones.getAttribute("aria-expanded") === "true";
        cerrarCuenta();
        cerrarNavegacionMovil();
        botonNotificaciones.setAttribute("aria-expanded", String(!abierto));
        if (panelNotificaciones) panelNotificaciones.hidden = abierto;
    });

    botonCuenta?.addEventListener("click", () => {
        const abierto = botonCuenta.getAttribute("aria-expanded") === "true";
        cerrarNotificaciones();
        cerrarNavegacionMovil();
        botonCuenta.setAttribute("aria-expanded", String(!abierto));
        if (panelCuenta) panelCuenta.hidden = abierto;
    });

    document.addEventListener("click", (evento) => {
        if (notificaciones && !notificaciones.contains(evento.target)) {
            cerrarNotificaciones();
        }
        if (menuCuenta && !menuCuenta.contains(evento.target)) {
            cerrarCuenta();
        }
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key !== "Escape") return;

        if (botonCuenta?.getAttribute("aria-expanded") === "true") {
            cerrarCuenta();
            botonCuenta.focus();
        } else if (botonNotificaciones?.getAttribute("aria-expanded") === "true") {
            cerrarNotificaciones();
            botonNotificaciones.focus();
        }
    });
});
