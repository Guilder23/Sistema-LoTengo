document.addEventListener("DOMContentLoaded", () => {
    const nombre = document.querySelector("#id_nombre");
    const slug = document.querySelector("#id_slug");
    if (!nombre || !slug) return;

    let slugEditado = Boolean(slug.value);
    slug.addEventListener("input", () => {
        slugEditado = slug.value.length > 0;
    });
    nombre.addEventListener("input", () => {
        if (slugEditado) return;
        slug.value = nombre.value
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "");
    });
});
