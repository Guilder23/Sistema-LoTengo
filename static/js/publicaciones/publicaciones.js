document.querySelector("[data-limpiar-filtros]")?.addEventListener("click", () => {
    const form = document.querySelector(".filtros-publicaciones");
    if (form) {
        window.location.assign(form.action);
    }
});

document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
        if (!window.confirm(formulario.dataset.confirmar)) {
            evento.preventDefault();
        }
    });
});
