document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
        if (!window.confirm(formulario.dataset.confirmar)) {
            evento.preventDefault();
        }
    });
});

const galeria = document.querySelector("[data-galeria-detalle]");
const imagenPrincipal = galeria?.querySelector("[data-galeria-imagen-principal]");
const contadorGaleria = galeria?.querySelector("[data-galeria-contador]");
const miniaturas = galeria?.querySelectorAll("[data-galeria-miniatura]");

miniaturas?.forEach((miniatura, indice) => {
    miniatura.addEventListener("click", () => {
        if (!imagenPrincipal) return;

        imagenPrincipal.src = miniatura.dataset.src;
        imagenPrincipal.alt = miniatura.dataset.alt;
        miniaturas.forEach((elemento, indiceActual) => {
            const activa = indiceActual === indice;
            elemento.classList.toggle("is-activa", activa);
            elemento.setAttribute("aria-pressed", String(activa));
        });
        if (contadorGaleria) {
            contadorGaleria.textContent = `${indice + 1} / ${miniaturas.length}`;
        }
    });
});
