document.addEventListener("DOMContentLoaded", () => {
    const layout = document.querySelector(".cuenta-espacio");
    const sidebar = layout?.querySelector(".cuenta-sidebar");
    const compactButton = sidebar?.querySelector(".sidebar-toggle");
    const drawerTrigger = document.querySelector("[data-sidebar-drawer-trigger]");
    const backdrop = layout?.querySelector("[data-sidebar-cerrar]");
    const content = layout?.querySelector(".cuenta-espacio-contenido");
    const navbar = document.querySelector(".navbar-con-sidebar");

    if (!layout || !sidebar || !compactButton || !backdrop) {
        return;
    }

    const mobileQuery = window.matchMedia("(max-width: 767.98px)");
    let isMobile = mobileQuery.matches;

    function setCollapsed(collapsed) {
        layout.classList.toggle("is-sidebar-collapsed", collapsed);
        navbar?.classList.toggle("is-sidebar-collapsed", collapsed);
        compactButton.setAttribute("aria-expanded", String(!collapsed));
        const label = collapsed ? "Expandir menú lateral" : "Contraer menú lateral";
        compactButton.setAttribute("aria-label", label);
        compactButton.title = label;
    }

    // En móvil el panel se abre sobre la página; en escritorio conserva su modo compacto.
    function setDrawerOpen(open, returnFocus = false) {
        const shouldOpen = isMobile && open;
        layout.classList.toggle("is-sidebar-open", shouldOpen);
        backdrop.hidden = !shouldOpen;
        document.body.classList.toggle("cuenta-sidebar-abierto", shouldOpen);

        sidebar.setAttribute("aria-hidden", String(isMobile && !shouldOpen));
        sidebar.inert = isMobile && !shouldOpen;
        if (content) content.inert = shouldOpen;
        if (navbar) navbar.inert = shouldOpen;

        drawerTrigger?.setAttribute("aria-expanded", String(shouldOpen));
        drawerTrigger?.setAttribute(
            "aria-label",
            shouldOpen ? "Cerrar opciones de Mi cuenta" : "Abrir opciones de Mi cuenta"
        );

        if (isMobile) {
            compactButton.setAttribute("aria-expanded", String(shouldOpen));
            const label = shouldOpen ? "Cerrar menú de cuenta" : "Abrir menú de cuenta";
            compactButton.setAttribute("aria-label", label);
            compactButton.title = label;
        }

        if (shouldOpen) {
            compactButton.focus();
        } else if (returnFocus) {
            drawerTrigger?.focus();
        }
    }

    setCollapsed(false);
    setDrawerOpen(false);

    drawerTrigger?.addEventListener("click", () => {
        setDrawerOpen(!layout.classList.contains("is-sidebar-open"), true);
    });

    compactButton.addEventListener("click", () => {
        if (isMobile) {
            setDrawerOpen(false, true);
            return;
        }
        setCollapsed(!layout.classList.contains("is-sidebar-collapsed"));
    });

    backdrop.addEventListener("click", () => setDrawerOpen(false, true));

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && layout.classList.contains("is-sidebar-open")) {
            setDrawerOpen(false, true);
        }
    });

    window.addEventListener("resize", () => {
        const mobileMode = mobileQuery.matches;
        if (mobileMode === isMobile) {
            return;
        }
        isMobile = mobileMode;
        setCollapsed(false);
        setDrawerOpen(false);
    });
});
