document.addEventListener("DOMContentLoaded", () => {
    const filterButton = document.querySelector("[data-marketplace-filter]");
    const sidebar = document.getElementById("marketplace-sidebar");

    if (filterButton && sidebar) {
        filterButton.addEventListener("click", () => {
            const isExpanded = filterButton.getAttribute("aria-expanded") === "true";
            filterButton.setAttribute("aria-expanded", String(!isExpanded));
            sidebar.classList.toggle("is-open", !isExpanded);
        });

        document.addEventListener("keydown", (event) => {
            if (event.key !== "Escape" || filterButton.getAttribute("aria-expanded") !== "true") return;
            filterButton.setAttribute("aria-expanded", "false");
            sidebar.classList.remove("is-open");
            filterButton.focus();
        });
    }

    const gallery = document.querySelector("[data-galeria-detalle]");
    const mainImage = gallery?.querySelector("[data-galeria-imagen-principal]");
    const counter = gallery?.querySelector("[data-galeria-contador]");
    const thumbnails = gallery?.querySelectorAll("[data-galeria-miniatura]");

    thumbnails?.forEach((thumbnail, index) => {
        thumbnail.addEventListener("click", () => {
            if (!mainImage) return;

            mainImage.src = thumbnail.dataset.src;
            mainImage.alt = thumbnail.dataset.alt;
            thumbnails.forEach((item, currentIndex) => {
                const isActive = currentIndex === index;
                item.classList.toggle("is-activa", isActive);
                item.setAttribute("aria-pressed", String(isActive));
            });
            if (counter) counter.textContent = `${index + 1} / ${thumbnails.length}`;
        });
    });
});
