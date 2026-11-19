document.addEventListener("DOMContentLoaded", () => {
    const layout = document.querySelector(".cuenta-espacio");
    const button = layout?.querySelector(".sidebar-toggle");
    if (!layout || !button) return;
    const navbar = document.querySelector(".navbar-con-sidebar");

    const setCollapsed = (collapsed) => {
        layout.classList.toggle("is-sidebar-collapsed", collapsed);
        navbar?.classList.toggle("is-sidebar-collapsed", collapsed);
        button.setAttribute("aria-expanded", String(!collapsed));
        const label = collapsed ? "Expandir menú lateral" : "Contraer menú lateral";
        button.setAttribute("aria-label", label);
        button.title = label;
    };

    setCollapsed(window.matchMedia("(max-width: 767.98px)").matches);

    button.addEventListener("click", () => {
        setCollapsed(!layout.classList.contains("is-sidebar-collapsed"));
    });
});