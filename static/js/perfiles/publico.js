document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-marketplace-filter]").forEach((button) => {
        const sidebar = document.querySelector("#marketplace-sidebar");
        if (!sidebar) return;

        button.addEventListener("click", () => {
            const open = !sidebar.classList.contains("is-open");
            sidebar.classList.toggle("is-open", open);
            button.setAttribute("aria-expanded", String(open));
            document.body.classList.toggle("marketplace-sidebar-open", open);
        });
    });
});
