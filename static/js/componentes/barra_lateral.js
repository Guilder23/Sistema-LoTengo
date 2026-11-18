document.addEventListener("DOMContentLoaded", () => {
    const layout = document.querySelector(".cuenta-panel-layout");
    const button = layout?.querySelector(".sidebar-toggle");
    if (!layout || !button) return;

    const setCollapsed = (collapsed) => {
        layout.classList.toggle("is-sidebar-collapsed", collapsed);
        button.setAttribute("aria-expanded", String(!collapsed));
        const label = collapsed ? "Expandir menú lateral" : "Contraer menú lateral";
        button.setAttribute("aria-label", label);
        button.title = label;
    };

    button.addEventListener("click", () => {
        setCollapsed(!layout.classList.contains("is-sidebar-collapsed"));
    });
});