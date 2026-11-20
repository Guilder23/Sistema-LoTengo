document.addEventListener("DOMContentLoaded", () => {
    const entradaFoto = document.querySelector("[data-perfil-foto]");
    const eliminarFoto = document.querySelector("[data-eliminar-foto]");
    const vistaPrevia = document.querySelector("[data-foto-preview]");
    const inicial = document.querySelector("[data-avatar-inicial]");
    const nombreFoto = document.querySelector("[data-foto-nombre]");
    const formulario = document.querySelector("[data-perfil-formulario]");
    const botonGuardar = document.querySelector("[data-perfil-guardar]");

    if (!entradaFoto || !vistaPrevia || !inicial || !formulario) return;

    const fotoOriginal = vistaPrevia.dataset.fotoOriginal || "";
    let urlTemporal = "";

    const limpiarVistaTemporal = () => {
        if (!urlTemporal) return;
        URL.revokeObjectURL(urlTemporal);
        urlTemporal = "";
    };

    const mostrarFotoOriginal = () => {
        limpiarVistaTemporal();
        if (fotoOriginal && !eliminarFoto?.checked) {
            vistaPrevia.src = fotoOriginal;
            vistaPrevia.hidden = false;
            inicial.hidden = true;
            return;
        }
        vistaPrevia.removeAttribute("src");
        vistaPrevia.hidden = true;
        inicial.hidden = false;
    };

    entradaFoto.addEventListener("change", () => {
        const archivo = entradaFoto.files?.[0];
        if (!archivo) {
            mostrarFotoOriginal();
            if (nombreFoto) {
                nombreFoto.textContent = "La vista previa se actualizará al elegir una imagen.";
            }
            return;
        }

        limpiarVistaTemporal();
        if (eliminarFoto) eliminarFoto.checked = false;
        urlTemporal = URL.createObjectURL(archivo);
        vistaPrevia.src = urlTemporal;
        vistaPrevia.hidden = false;
        inicial.hidden = true;
        if (nombreFoto) nombreFoto.textContent = archivo.name;
    });

    eliminarFoto?.addEventListener("change", () => {
        if (eliminarFoto.checked) {
            entradaFoto.value = "";
            if (nombreFoto) nombreFoto.textContent = "Se quitará la foto actual al guardar.";
        } else if (nombreFoto) {
            nombreFoto.textContent = "La vista previa se actualizará al elegir una imagen.";
        }
        mostrarFotoOriginal();
    });

    formulario.addEventListener("submit", () => {
        if (!botonGuardar) return;
        botonGuardar.disabled = true;
        botonGuardar.textContent = "Guardando…";
    });

    window.addEventListener("pagehide", limpiarVistaTemporal, { once: true });
});
