document.addEventListener("DOMContentLoaded", () => {
    const lista = document.querySelector("[data-lista-conversaciones]");
    if (!lista) return;

    const busqueda = document.querySelector("[data-buscar-conversacion]");
    const sinResultados = document.querySelector("[data-sin-resultados]");
    const filtros = [...document.querySelectorAll("[data-filtro-chat]")];
    const conversaciones = [...lista.querySelectorAll("[data-conversacion]")];
    let filtroActivo = "todos";

    const filtrar = () => {
        const termino = (busqueda?.value || "").trim().toLocaleLowerCase();
        let visibles = 0;

        conversaciones.forEach((conversacion) => {
            const coincideTexto = (conversacion.dataset.busqueda || "")
                .toLocaleLowerCase()
                .includes(termino);
            const coincideFiltro = filtroActivo === "todos"
                || conversacion.dataset.noLeidos === "true";
            conversacion.hidden = !coincideTexto || !coincideFiltro;
            if (!conversacion.hidden) visibles += 1;
        });

        if (sinResultados) {
            sinResultados.hidden = conversaciones.length === 0 || visibles > 0;
        }
    };

    busqueda?.addEventListener("input", filtrar);
    document.addEventListener("chat-contadores-actualizados", filtrar);
    filtros.forEach((boton) => {
        boton.addEventListener("click", () => {
            filtroActivo = boton.dataset.filtroChat || "todos";
            filtros.forEach((filtro) => {
                const activo = filtro === boton;
                filtro.classList.toggle("is-active", activo);
                filtro.setAttribute("aria-pressed", String(activo));
            });
            filtrar();
        });
    });

    filtrar();
});
