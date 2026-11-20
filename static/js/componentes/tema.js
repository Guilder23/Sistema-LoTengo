(() => {
    const claveTema = "lotengo-tema";
    const temasValidos = new Set(["claro", "oscuro"]);

    const leerTemaGuardado = () => {
        try {
            const tema = window.localStorage.getItem(claveTema);
            return temasValidos.has(tema) ? tema : "claro";
        } catch (error) {
            console.error("No se pudo leer la preferencia de tema.", error);
            return "claro";
        }
    };

    const aplicarTema = (tema, guardar = false) => {
        const temaAplicado = temasValidos.has(tema) ? tema : "claro";
        document.documentElement.dataset.tema = temaAplicado;
        document.documentElement.style.colorScheme = temaAplicado === "oscuro"
            ? "dark"
            : "light";

        const botonTema = document.querySelector("[data-cambiar-tema]");
        const textoBoton = botonTema?.querySelector("[data-etiqueta-tema]");
        const temaSiguiente = temaAplicado === "oscuro" ? "claro" : "oscuro";
        const etiqueta = `Cambiar a modo ${temaSiguiente}`;

        if (botonTema) {
            botonTema.setAttribute("aria-pressed", String(temaAplicado === "oscuro"));
            botonTema.setAttribute("aria-label", etiqueta);
            botonTema.title = etiqueta;
        }
        if (textoBoton) textoBoton.textContent = etiqueta;

        if (guardar) {
            try {
                window.localStorage.setItem(claveTema, temaAplicado);
            } catch (error) {
                console.error("No se pudo guardar la preferencia de tema.", error);
            }
        }
    };

    aplicarTema(leerTemaGuardado());

    document.addEventListener("DOMContentLoaded", () => {
        const botonTema = document.querySelector("[data-cambiar-tema]");
        botonTema?.addEventListener("click", () => {
            const temaActual = document.documentElement.dataset.tema;
            aplicarTema(temaActual === "oscuro" ? "claro" : "oscuro", true);
        });
    });

    window.addEventListener("storage", (evento) => {
        if (evento.key === claveTema) aplicarTema(leerTemaGuardado());
    });
})();
