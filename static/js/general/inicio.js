document.addEventListener("DOMContentLoaded", () => {
    const filterButton = document.querySelector("[data-marketplace-filter]");
    const sidebar = document.getElementById("marketplace-sidebar");

    if (!filterButton || !sidebar) return;

    filterButton.addEventListener("click", () => {
        const isExpanded = filterButton.getAttribute("aria-expanded") === "true";
        filterButton.setAttribute("aria-expanded", String(!isExpanded));
        sidebar.classList.toggle("is-open", !isExpanded);
    });
});
