(() => {
    // Filtra las filas cargadas en la pagina, sin hacer una nueva consulta.
    function inicializarFiltro() {
        const entrada = document.querySelector("#buscar-catalogo");
        const filas = [...document.querySelectorAll("[data-fila-catalogo]")];
        const vacio = document.querySelector("#sin-resultados");
        if (!entrada || filas.length === 0) return;

        entrada.addEventListener("input", () => {
            const consulta = entrada.value.trim().toLocaleLowerCase();
            let visibles = 0;
            filas.forEach((fila) => {
                const coincide = (fila.dataset.terminos || fila.textContent)
                    .toLocaleLowerCase()
                    .includes(consulta);
                fila.hidden = !coincide;
                if (coincide) visibles += 1;
            });
            if (vacio) vacio.hidden = visibles > 0;
        });
    }

    // Solicita confirmacion antes de acciones administrativas sensibles.
    function confirmarEnvio() {
        document.querySelectorAll("form[data-confirmacion]").forEach((formulario) => {
            formulario.addEventListener("submit", (evento) => {
                if (!window.confirm(formulario.dataset.confirmacion)) {
                    evento.preventDefault();
                }
            });
        });
    }

    // Permite copiar identificadores y anuncia el resultado.
    function activarCopiado() {
        document.querySelectorAll("[data-copiar]").forEach((boton) => {
            boton.addEventListener("click", async () => {
                try {
                    await navigator.clipboard.writeText(boton.dataset.copiar);
                    boton.textContent = "Copiado";
                } catch {
                    const estado = boton.parentElement.querySelector("[data-copiar-estado]");
                    if (estado) {
                        estado.textContent = "No se pudo copiar; selecciona el valor y cópialo manualmente.";
                    }
                }
            });
        });
    }

    window.LotengoCatalogos = { inicializarFiltro, confirmarEnvio, activarCopiado };
})();

document.addEventListener("DOMContentLoaded", () => {
    window.LotengoCatalogos.inicializarFiltro();
});
