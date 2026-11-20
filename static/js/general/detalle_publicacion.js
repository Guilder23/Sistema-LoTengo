document.addEventListener("DOMContentLoaded", () => {
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
