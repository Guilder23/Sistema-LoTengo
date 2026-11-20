const selectorDepartamento = document.querySelector('select[name="departamento"]');
const selectorMunicipio = document.querySelector('select[name="municipio"]');
const modalTipo = document.querySelector("[data-modal-tipo]");
const formularioPublicacion = document.querySelector("[data-formulario-publicacion]");
const selectorTipo = document.querySelector("[data-tipo-publicacion-input]");
const resumenTipo = document.querySelector("[data-tipo-publicacion-resumen]");
const opcionesTipo = document.querySelectorAll("[data-tipo-publicacion]");
const botonCambiarTipo = document.querySelector("[data-cambiar-tipo]");

function mostrarModalTipo() {
    if (typeof modalTipo.showModal === "function") {
        if (!modalTipo.open) {
            modalTipo.showModal();
        }
    } else {
        modalTipo.setAttribute("open", "");
    }
}

function ocultarModalTipo() {
    if (typeof modalTipo.close === "function" && modalTipo.open) {
        modalTipo.close();
    } else {
        modalTipo.removeAttribute("open");
    }
}

if (modalTipo && formularioPublicacion && selectorTipo && resumenTipo) {
    if (formularioPublicacion.hidden) {
        mostrarModalTipo();
    }

    opcionesTipo.forEach((opcion) => {
        opcion.addEventListener("click", () => {
            selectorTipo.value = opcion.dataset.tipoPublicacion;
            resumenTipo.textContent = opcion.dataset.etiquetaTipo;
            formularioPublicacion.hidden = false;
            formularioPublicacion.dispatchEvent(new Event("formulario:visible"));
            ocultarModalTipo();
            formularioPublicacion.querySelector("select, input:not([type='hidden']), textarea")?.focus();
        });
    });

    botonCambiarTipo?.addEventListener("click", mostrarModalTipo);

    modalTipo.addEventListener("cancel", (evento) => {
        if (!selectorTipo.value) {
            evento.preventDefault();
        }
    });
}

async function actualizarMunicipios() {
    if (!selectorDepartamento || !selectorMunicipio) {
        return;
    }

    const departamento = selectorDepartamento.value;
    const municipioSeleccionado = selectorMunicipio.value;
    selectorMunicipio.replaceChildren();
    const opcionInicial = document.createElement("option");
    opcionInicial.value = "";
    opcionInicial.textContent = departamento
        ? "Selecciona un municipio"
        : "Selecciona primero un departamento";
    selectorMunicipio.append(opcionInicial);
    selectorMunicipio.disabled = !departamento;

    if (!departamento) {
        return;
    }

    const respuesta = await fetch(
        `/publicaciones/municipios/?departamento=${encodeURIComponent(departamento)}`
    );
    if (!respuesta.ok) {
        return;
    }
    const datos = await respuesta.json();
    datos.municipios.forEach((municipio) => {
        const opcion = document.createElement("option");
        opcion.value = municipio;
        opcion.textContent = municipio;
        opcion.selected = municipio === municipioSeleccionado;
        selectorMunicipio.append(opcion);
    });
}

selectorDepartamento?.addEventListener("change", () => {
    selectorMunicipio.value = "";
    actualizarMunicipios();
});
actualizarMunicipios();

// Controla los pasos y valida cada sección antes de avanzar.
(() => {
    const formulario = document.querySelector(".formulario-publicacion");
    const progreso = formulario?.querySelector("[data-progreso-formulario]");

    if (!formulario || !progreso) {
        return;
    }

    const pasos = Array.from(progreso.querySelectorAll("[data-paso-formulario]"));
    const porcentajeProgreso = progreso.querySelector("[data-progreso-porcentaje]");
    const textoProgreso = progreso.querySelector("[data-progreso-texto]");
    const barraProgreso = progreso.querySelector("[data-progreso-barra]");
    const barraContenedor = barraProgreso.parentElement;
    const todosLosContenedores = Array.from(
        formulario.querySelectorAll("[data-paso-formulario-contenedor]")
    );
    const contenedoresPorPaso = pasos.map((paso) =>
        todosLosContenedores.filter(
            (contenedor) =>
                contenedor.dataset.pasoFormularioContenedor === paso.dataset.pasoFormulario
        )
    );

    if (contenedoresPorPaso.some((contenedores) => contenedores.length === 0)) {
        return;
    }

    function primerCampoInvalido(contenedores) {
        for (const contenedor of contenedores) {
            const campos = contenedor.querySelectorAll("input, select, textarea");
            for (const campo of campos) {
                if (!campo.disabled && campo.type !== "hidden" && !campo.checkValidity()) {
                    return campo;
                }
            }
        }
        return null;
    }

    function contieneErrores(contenedores) {
        return contenedores.some((contenedor) => contenedor.querySelector(".campo-error"));
    }

    function actualizarIndicador(indice) {
        const total = pasos.length;
        const porcentaje = Math.round(((indice + 1) / total) * 100);

        textoProgreso.textContent = `Paso ${indice + 1} de ${total}: ${pasos[indice].dataset.etiquetaPaso}`;
        porcentajeProgreso.textContent = `${porcentaje}%`;
        barraProgreso.style.width = `${porcentaje}%`;
        barraContenedor.setAttribute("aria-valuenow", String(indice + 1));

        pasos.forEach((paso, pasoIndice) => {
            if (pasoIndice === indice) {
                paso.setAttribute("aria-current", "step");
            } else {
                paso.removeAttribute("aria-current");
            }
            const bloqueado = pasoIndice > pasoActualMaximo;
            paso.setAttribute("aria-disabled", String(bloqueado));
            paso.tabIndex = bloqueado ? -1 : 0;
        });
    }

    let pasoActual = 0;
    const indiceConError = contenedoresPorPaso.findIndex(contieneErrores);
    let pasoActualMaximo = Math.max(0, indiceConError);

    function mostrarPaso(indice, enfocar = false, desplazar = false) {
        pasoActual = indice;
        todosLosContenedores.forEach((contenedor) => {
            contenedor.hidden = !contenedoresPorPaso[indice].includes(contenedor);
        });
        actualizarIndicador(indice);

        if (desplazar) {
            const movimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches
                ? "auto"
                : "smooth";
            progreso.scrollIntoView({ behavior: movimiento, block: "start" });
        }

        if (enfocar) {
            const encabezado = contenedoresPorPaso[indice]
                .map((contenedor) => contenedor.querySelector("h2"))
                .find(Boolean);
            if (encabezado) {
                encabezado.tabIndex = -1;
                encabezado.focus({ preventScroll: true });
            }
        }
    }

    function validarPaso(indice) {
        const invalido = primerCampoInvalido(contenedoresPorPaso[indice]);
        if (!invalido) {
            return true;
        }
        invalido.reportValidity();
        invalido.focus();
        return false;
    }

    pasos.forEach((paso, indice) => {
        paso.addEventListener("click", (evento) => {
            evento.preventDefault();
            if (indice <= pasoActualMaximo) {
                mostrarPaso(indice, true, true);
            }
        });
    });

    formulario.querySelectorAll("[data-siguiente-paso]").forEach((boton) => {
        boton.addEventListener("click", () => {
            if (!validarPaso(pasoActual)) {
                return;
            }
            const siguiente = pasoActual + 1;
            if (siguiente < pasos.length) {
                pasoActualMaximo = Math.max(pasoActualMaximo, siguiente);
                mostrarPaso(siguiente, true, true);
            }
        });
    });

    formulario.querySelectorAll("[data-paso-anterior]").forEach((boton) => {
        boton.addEventListener("click", () => {
            if (pasoActual > 0) {
                mostrarPaso(pasoActual - 1, true, true);
            }
        });
    });

    formulario.addEventListener("submit", (evento) => {
        for (let indice = 0; indice < pasos.length; indice += 1) {
            const invalido = primerCampoInvalido(contenedoresPorPaso[indice]);
            if (invalido) {
                evento.preventDefault();
                pasoActualMaximo = Math.max(pasoActualMaximo, indice);
                mostrarPaso(indice, false, true);
                window.requestAnimationFrame(() => {
                    invalido.reportValidity();
                    invalido.focus();
                });
                return;
            }
        }
    });

    formulario.querySelectorAll("details").forEach((detalle) => {
        if (detalle.querySelector(".campo-error")) {
            detalle.open = true;
        }
    });
    formulario.querySelectorAll("[data-siguiente-paso], [data-paso-anterior]").forEach((boton) => {
        boton.hidden = false;
    });
    formulario.addEventListener("formulario:visible", () => mostrarPaso(pasoActual));
    mostrarPaso(indiceConError >= 0 ? indiceConError : 0);

    formulario.querySelectorAll("[data-campo-contador]").forEach((campo) => {
        const contador = campo.closest("label")?.querySelector("[data-contador-caracteres]");
        if (!contador) {
            return;
        }
        const actualizarContador = () => {
            contador.textContent = String(campo.value.length);
        };
        campo.addEventListener("input", actualizarContador);
        actualizarContador();
    });
})();

// Mantiene el límite, la vista previa y la eliminación de imágenes nuevas.
(() => {
    const selectorImagenes = document.querySelector("#imagenesPublicacion");
    const vistaPreviaImagenes = document.querySelector("#vistaPreviaImagenes");
    const contenedorSubida = document.querySelector(".imagenes-subida");

    if (!selectorImagenes || !vistaPreviaImagenes || !contenedorSubida) {
        return;
    }

    const zonaSubida = contenedorSubida.querySelector("[data-zona-subida-imagenes]");
    const maximoImagenes = Number(contenedorSubida.dataset.maximoImagenes);
    const tamanoMaximo = Number(contenedorSubida.dataset.tamanoMaximoBytes);
    const conteoImagenes = contenedorSubida.querySelector("[data-conteo-imagenes]");
    const estadoSubida = contenedorSubida.querySelector("[data-estado-subida-imagenes]");
    const imagenesExistentes = Array.from(
        document.querySelectorAll("[data-imagen-existente]")
    );
    const archivosSeleccionados = [];
    let urlsPrevia = [];

    const alertaSubida = document.createElement("p");
    alertaSubida.className = "campo-error error-subida-imagenes";
    alertaSubida.setAttribute("role", "alert");
    alertaSubida.dataset.errorSubida = "";
    alertaSubida.hidden = true;
    contenedorSubida.append(alertaSubida);

    function cantidadExistenteActiva() {
        return imagenesExistentes.filter((elemento) => {
            const casilla = elemento.querySelector('input[name="eliminar_imagenes"]');
            return !casilla || !casilla.checked;
        }).length;
    }

    function actualizarEstado() {
        const total = cantidadExistenteActiva() + archivosSeleccionados.length;
        const restante = maximoImagenes - cantidadExistenteActiva();
        conteoImagenes.textContent = `${total} de ${maximoImagenes}`;
        estadoSubida.textContent = archivosSeleccionados.length
            ? `${archivosSeleccionados.length} imagen${archivosSeleccionados.length === 1 ? "" : "es"} nueva${archivosSeleccionados.length === 1 ? "" : "s"} lista${archivosSeleccionados.length === 1 ? "" : "s"} para guardar.`
            : imagenesExistentes.length
                ? "No agregaste imágenes nuevas."
                : "Aún no agregaste fotografías.";
        selectorImagenes.disabled = restante <= archivosSeleccionados.length;
        zonaSubida.setAttribute(
            "aria-disabled",
            selectorImagenes.disabled ? "true" : "false"
        );
        zonaSubida.classList.toggle("zona-subida-deshabilitada", selectorImagenes.disabled);
    }

    function actualizarArchivosInput() {
        const transferencia = new DataTransfer();
        archivosSeleccionados.forEach((archivo) => transferencia.items.add(archivo));
        selectorImagenes.files = transferencia.files;
    }

    function mostrarPrevisualizaciones() {
        urlsPrevia.forEach((url) => URL.revokeObjectURL(url));
        urlsPrevia = [];
        vistaPreviaImagenes.replaceChildren();

        archivosSeleccionados.forEach((archivo, indice) => {
            const tarjeta = document.createElement("figure");
            tarjeta.className = "imagen-previsualizacion";

            const imagen = document.createElement("img");
            imagen.alt = `Vista previa: ${archivo.name}`;
            imagen.src = URL.createObjectURL(archivo);
            urlsPrevia.push(imagen.src);

            const pie = document.createElement("figcaption");
            pie.className = "imagen-previsualizacion-pie";

            const nombre = document.createElement("span");
            nombre.textContent = archivo.name;

            const quitar = document.createElement("button");
            quitar.className = "imagen-previsualizacion-quitar";
            quitar.type = "button";
            quitar.textContent = "Quitar";
            quitar.setAttribute("aria-label", `Quitar ${archivo.name}`);
            quitar.addEventListener("click", () => {
                archivosSeleccionados.splice(indice, 1);
                actualizarArchivosInput();
                mostrarPrevisualizaciones();
                actualizarEstado();
            });

            pie.append(nombre, quitar);
            tarjeta.append(imagen, pie);
            vistaPreviaImagenes.append(tarjeta);
        });
    }

    function agregarArchivos(archivos) {
        alertaSubida.hidden = true;
        alertaSubida.textContent = "";
        const extensionesPermitidas = /\.(jpe?g|png|webp)$/i;
        const errores = [];

        Array.from(archivos).forEach((archivo) => {
            if (!extensionesPermitidas.test(archivo.name)) {
                errores.push(`${archivo.name}: usa un archivo JPG, PNG o WEBP.`);
                return;
            }
            if (archivo.size > tamanoMaximo) {
                errores.push(`${archivo.name}: supera el límite de ${Math.floor(tamanoMaximo / 1048576)} MB.`);
                return;
            }
            if (cantidadExistenteActiva() + archivosSeleccionados.length >= maximoImagenes) {
                errores.push(`Puedes adjuntar hasta ${maximoImagenes} fotografías en total.`);
                return;
            }
            archivosSeleccionados.push(archivo);
        });

        if (errores.length) {
            alertaSubida.textContent = errores.join(" ");
            alertaSubida.hidden = false;
        }

        actualizarArchivosInput();
        mostrarPrevisualizaciones();
        actualizarEstado();
    }

    selectorImagenes.addEventListener("change", (evento) => {
        agregarArchivos(evento.target.files);
    });

    zonaSubida.addEventListener("dragover", (evento) => {
        evento.preventDefault();
        if (!selectorImagenes.disabled) {
            zonaSubida.classList.add("zona-subida-arrastrando");
        }
    });

    zonaSubida.addEventListener("dragleave", () => {
        zonaSubida.classList.remove("zona-subida-arrastrando");
    });

    zonaSubida.addEventListener("drop", (evento) => {
        evento.preventDefault();
        zonaSubida.classList.remove("zona-subida-arrastrando");
        if (!selectorImagenes.disabled) {
            agregarArchivos(evento.dataTransfer.files);
        }
    });

    imagenesExistentes.forEach((elemento) => {
        const casilla = elemento.querySelector('input[name="eliminar_imagenes"]');
        const etiqueta = elemento.querySelector("[data-etiqueta-quitar-imagen]");
        casilla.addEventListener("change", () => {
            elemento.classList.toggle("imagen-marcada-eliminar", casilla.checked);
            etiqueta.textContent = casilla.checked ? "Se quitará · Deshacer" : "Quitar";
            actualizarEstado();
        });
        if (casilla.checked) {
            elemento.classList.add("imagen-marcada-eliminar");
        }
    });

    const conoceLugarExacto = document.querySelector("[data-conoce-lugar-exacto]");
    const referenciaPrivada = document.querySelector("[data-referencia-privada]");
    if (conoceLugarExacto && referenciaPrivada) {
        conoceLugarExacto.addEventListener("change", () => {
            referenciaPrivada.hidden = !conoceLugarExacto.checked;
            if (!conoceLugarExacto.checked) {
                referenciaPrivada.querySelector("input").value = "";
            }
        });
    }

    actualizarEstado();
})();
