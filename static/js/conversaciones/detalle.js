document.addEventListener("DOMContentLoaded", () => {
    const chat = document.querySelector("[data-chat-root]");
    if (!chat) return;

    const mensajes = chat.querySelector("[data-chat-mensajes]");
    const formulario = chat.querySelector("[data-chat-form]");
    const campo = chat.querySelector("[data-chat-contenido]");
    const contador = chat.querySelector("[data-chat-contador]");
    const error = chat.querySelector("[data-chat-error]");
    const botonEnviar = chat.querySelector(".messenger-enviar");
    const entradaArchivo = chat.querySelector("[data-chat-archivo]");
    const vistaAdjunto = chat.querySelector("[data-chat-adjunto]");
    const vistaImagen = chat.querySelector("[data-chat-vista-imagen]");
    const vistaAudio = chat.querySelector("[data-chat-vista-audio]");
    const nombreAdjunto = chat.querySelector("[data-chat-adjunto-nombre]");
    const botonQuitarAdjunto = chat.querySelector("[data-chat-quitar-adjunto]");
    const botonGrabar = chat.querySelector("[data-chat-grabar]");
    const estadoGrabacion = chat.querySelector("[data-chat-grabacion]");
    const cronometro = chat.querySelector("[data-chat-cronometro]");
    const botonCargarAnteriores = chat.querySelector("[data-chat-cargar-anteriores]");
    const botonBajar = chat.querySelector("[data-chat-bajar]");
    const usuarioId = chat.dataset.chatUsuario;
    const conversacionesId = chat.dataset.chatConversacion;
    const pendientes = new Map();
    const temporizadoresPendientes = new Map();
    let archivoPendiente = null;
    let urlVistaPrevia = "";
    let grabadora = null;
    let flujoAudio = null;
    let intervaloGrabacion = null;
    let inicioGrabacion = 0;
    let solicitandoMicrofono = false;
    let socket = null;
    let reconexion = null;
    let esperaReconexion = 1000;
    let cerrarAlSalir = false;
    let subiendoAdjunto = false;
    let seguirAlFinal = true;

    const mostrarError = (texto = "") => {
        if (error) error.textContent = texto;
    };

    const mantenerChatAlFinal = () => {
        if (seguirAlFinal) mensajes.scrollTop = mensajes.scrollHeight;
    };

    const actualizarContador = () => {
        if (!campo || !contador) return;
        contador.textContent = `${campo.value.length}/${campo.maxLength} · Enter para enviar · Shift + Enter para salto de línea`;
        campo.style.height = "auto";
        campo.style.height = `${Math.min(campo.scrollHeight, 132)}px`;
    };

    const urlAdjuntoSegura = (ruta) => {
        if (!ruta) return "";
        try {
            const url = new URL(ruta, window.location.origin);
            return url.origin === window.location.origin ? url.href : "";
        } catch {
            return "";
        }
    };

    const crearElementoMensaje = (mensaje) => {
        const propio = String(mensaje.remitente_id) === String(usuarioId);
        const elemento = document.createElement("article");
        elemento.className = `messenger-mensaje${propio ? " es-propio" : ""}`;
        elemento.dataset.mensaje = "";
        elemento.dataset.mensajeId = String(mensaje.id);
        elemento.dataset.remitenteId = String(mensaje.remitente_id);

        const burbuja = document.createElement("div");
        burbuja.className = "messenger-burbuja";
        const url = urlAdjuntoSegura(mensaje.adjunto_url);

        if (url && mensaje.tipo_adjunto === "imagen") {
            burbuja.classList.add("messenger-burbuja-imagen");
            const enlace = document.createElement("a");
            enlace.className = "messenger-imagen-enlace";
            enlace.href = url;
            enlace.target = "_blank";
            enlace.rel = "noopener";
            const imagen = document.createElement("img");
            imagen.src = url;
            imagen.alt = "Imagen enviada en la conversación";
            imagen.loading = "lazy";
            enlace.append(imagen);
            burbuja.append(enlace);
        } else if (url && mensaje.tipo_adjunto === "audio") {
            const audio = document.createElement("audio");
            audio.controls = true;
            audio.preload = "metadata";
            audio.src = url;
            audio.setAttribute("aria-label", "Audio enviado en la conversación");
            burbuja.append(audio);
        }

        if (mensaje.contenido) {
            const texto = document.createElement("p");
            texto.textContent = mensaje.contenido;
            burbuja.append(texto);
        }

        const hora = document.createElement("time");
        hora.dateTime = mensaje.enviada_en || "";
        hora.textContent = mensaje.hora_la_paz;
        burbuja.append(hora);
        elemento.append(burbuja);
        return elemento;
    };

    const yaExiste = (id) => [...mensajes.querySelectorAll("[data-mensaje]")]
        .some((elemento) => elemento.dataset.mensajeId === String(id));

    const actualizarUltimoMensaje = (mensaje) => {
        const ruta = `/conversaciones/${conversacionesId}/`;
        const enlace = [...document.querySelectorAll("[data-conversacion]")]
            .find((elemento) => new URL(elemento.href).pathname === ruta);
        if (!enlace) return;
        const texto = enlace.querySelector(".messenger-conversacion-ultimo");
        if (!texto) return;

        const propio = String(mensaje.remitente_id) === String(usuarioId);
        let resumen = mensaje.contenido || "";
        if (!resumen && mensaje.tipo_adjunto === "imagen") resumen = "Foto";
        if (!resumen && mensaje.tipo_adjunto === "audio") resumen = "Audio";
        texto.textContent = propio ? `Tú: ${resumen}` : resumen;

        const hora = enlace.querySelector("time");
        if (hora) {
            hora.dateTime = mensaje.enviada_en || "";
            hora.textContent = mensaje.hora_la_paz;
        }
    };

    const agregarMensaje = (mensaje, alFinal = true) => {
        if (!mensaje || yaExiste(mensaje.id)) return;
        chat.querySelector("[data-chat-vacio]")?.remove();

        const cercaDelFinal = mensajes.scrollHeight - mensajes.scrollTop - mensajes.clientHeight < 120;
        const elemento = crearElementoMensaje(mensaje);
        if (alFinal) {
            const botonNuevos = mensajes.querySelector("[data-chat-bajar]");
            if (botonNuevos) botonNuevos.before(elemento);
            else mensajes.append(elemento);
        } else {
            const botonAnterior = mensajes.querySelector("[data-chat-cargar-anteriores]");
            if (botonAnterior) botonAnterior.after(elemento);
            else mensajes.prepend(elemento);
        }

        if (alFinal && cercaDelFinal) {
            seguirAlFinal = true;
            mensajes.scrollTop = mensajes.scrollHeight;
        } else if (alFinal) {
            seguirAlFinal = false;
            if (botonBajar) botonBajar.hidden = false;
        }
        actualizarUltimoMensaje(mensaje);
    };

    const limpiarAdjunto = () => {
        if (urlVistaPrevia) URL.revokeObjectURL(urlVistaPrevia);
        urlVistaPrevia = "";
        archivoPendiente = null;
        if (entradaArchivo) entradaArchivo.value = "";
        if (vistaImagen) {
            vistaImagen.removeAttribute("src");
            vistaImagen.hidden = true;
        }
        if (vistaAudio) {
            vistaAudio.pause();
            vistaAudio.removeAttribute("src");
            vistaAudio.load();
            vistaAudio.hidden = true;
        }
        if (nombreAdjunto) nombreAdjunto.textContent = "";
        if (vistaAdjunto) vistaAdjunto.hidden = true;
    };

    const prepararVistaAdjunto = (archivo) => {
        limpiarAdjunto();
        if (!archivo) return;
        archivoPendiente = archivo;
        urlVistaPrevia = URL.createObjectURL(archivo);
        if (archivo.type.startsWith("image/")) {
            vistaImagen.src = urlVistaPrevia;
            vistaImagen.hidden = false;
            nombreAdjunto.textContent = archivo.name || "Imagen adjunta";
        } else {
            vistaAudio.src = urlVistaPrevia;
            vistaAudio.hidden = false;
            nombreAdjunto.textContent = archivo.name || "Audio adjunto";
        }
        vistaAdjunto.hidden = false;
        mostrarError();
    };

    const actualizarEstado = (texto, estado) => {
        const elemento = chat.querySelector("[data-chat-estado]");
        if (!elemento) return;
        elemento.textContent = texto;
        elemento.dataset.estado = estado;
    };

    const recibirMensaje = (mensaje) => {
        if (mensaje.id_cliente && pendientes.has(mensaje.id_cliente)) {
            const contenidoPendiente = pendientes.get(mensaje.id_cliente);
            pendientes.delete(mensaje.id_cliente);
            clearTimeout(temporizadoresPendientes.get(mensaje.id_cliente));
            temporizadoresPendientes.delete(mensaje.id_cliente);
            if (campo.value === contenidoPendiente) {
                campo.value = "";
                actualizarContador();
            }
            mostrarError();
        }
        agregarMensaje(mensaje);
    };

    const conectar = () => {
        if (cerrarAlSalir) return;
        const url = new URL(chat.dataset.chatSocket, window.location.href);
        url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        actualizarEstado("Conectando…", "conectando");
        socket = new WebSocket(url);

        socket.addEventListener("open", () => {
            esperaReconexion = 1000;
            actualizarEstado("Conectado", "conectada");
        });

        socket.addEventListener("message", (evento) => {
            let datos;
            try {
                datos = JSON.parse(evento.data);
            } catch {
                mostrarError("El chat recibió una respuesta no válida.");
                return;
            }
            if (datos.tipo === "mensaje") {
                recibirMensaje(datos.mensaje);
            } else if (datos.tipo === "error") {
                const idCliente = datos.id_cliente;
                if (idCliente && pendientes.has(idCliente)) {
                    const contenido = pendientes.get(idCliente);
                    pendientes.delete(idCliente);
                    clearTimeout(temporizadoresPendientes.get(idCliente));
                    temporizadoresPendientes.delete(idCliente);
                    if (!campo.value.trim()) {
                        campo.value = contenido;
                        actualizarContador();
                    }
                }
                mostrarError(datos.mensaje || "No se pudo enviar el mensaje.");
            }
        });

        socket.addEventListener("close", (evento) => {
            if (cerrarAlSalir) return;
            if (evento.code === 4401 || evento.code === 4403 || evento.code === 4404) {
                actualizarEstado("No se pudo conectar", "desconectada");
                mostrarError("No se pudo autorizar la conexión. Recarga la página.");
                return;
            }
            actualizarEstado("Reconectando…", "desconectada");
            reconexion = setTimeout(conectar, esperaReconexion);
            esperaReconexion = Math.min(esperaReconexion * 2, 30000);
        });
    };

    const cargarAnteriores = async () => {
        const primero = mensajes.querySelector("[data-mensaje]");
        if (!primero || !botonCargarAnteriores) return;
        botonCargarAnteriores.disabled = true;
        const alturaAnterior = mensajes.scrollHeight;
        const posicionAnterior = mensajes.scrollTop;
        const url = new URL(chat.dataset.chatAnterioresUrl, window.location.href);
        url.searchParams.set("antes", primero.dataset.mensajeId);

        try {
            const respuesta = await fetch(url, {
                credentials: "same-origin",
                headers: { Accept: "application/json" },
            });
            const datos = await respuesta.json();
            if (!respuesta.ok) throw new Error(datos.error || "No se cargaron los mensajes.");

            const fragmento = document.createDocumentFragment();
            datos.mensajes.forEach((mensaje) => {
                if (!yaExiste(mensaje.id)) fragmento.append(crearElementoMensaje(mensaje));
            });
            botonCargarAnteriores.after(fragmento);
            chat.dataset.chatHayMas = String(datos.hay_mas);
            if (!datos.hay_mas || datos.mensajes.length === 0) {
                botonCargarAnteriores.remove();
            } else {
                botonCargarAnteriores.disabled = false;
            }
            mensajes.scrollTop = posicionAnterior + mensajes.scrollHeight - alturaAnterior;
        } catch (errorCarga) {
            mostrarError(errorCarga.message || "No se pudieron cargar los mensajes anteriores.");
            botonCargarAnteriores.disabled = false;
        }
    };

    const enviarAdjunto = async () => {
        if (!archivoPendiente || subiendoAdjunto) return;
        subiendoAdjunto = true;
        botonEnviar.disabled = true;
        campo.disabled = true;
        entradaArchivo.disabled = true;
        botonGrabar.disabled = true;
        formulario.setAttribute("aria-busy", "true");
        mostrarError("Enviando archivo…");

        const datos = new FormData(formulario);
        datos.delete("archivo");
        datos.append("archivo", archivoPendiente, archivoPendiente.name);
        try {
            const respuesta = await fetch(formulario.action, {
                method: "POST",
                body: datos,
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const resultado = await respuesta.json();
            if (!respuesta.ok) throw new Error(resultado.error || "No se pudo enviar el archivo.");

            recibirMensaje(resultado.mensaje);
            campo.value = "";
            limpiarAdjunto();
            actualizarContador();
            if (!resultado.tiempo_real) {
                mostrarError("Se guardó el mensaje, pero la conexión en vivo está temporalmente interrumpida.");
            } else {
                mostrarError();
            }
        } catch (errorEnvio) {
            mostrarError(errorEnvio.message || "No se pudo enviar el archivo. Inténtalo de nuevo.");
        } finally {
            subiendoAdjunto = false;
            botonEnviar.disabled = false;
            campo.disabled = false;
            entradaArchivo.disabled = false;
            botonGrabar.disabled = false;
            formulario.removeAttribute("aria-busy");
        }
    };

    formulario?.addEventListener("submit", (evento) => {
        if (grabadora && grabadora.state === "recording") {
            evento.preventDefault();
            mostrarError("Detén la grabación antes de enviar el audio.");
            return;
        }
        if (archivoPendiente) {
            evento.preventDefault();
            enviarAdjunto();
            return;
        }

        const contenido = campo.value.trim();
        if (!contenido) {
            evento.preventDefault();
            mostrarError("Escribe un mensaje o adjunta una imagen o un audio.");
            return;
        }
        if (socket?.readyState !== WebSocket.OPEN) return;

        evento.preventDefault();
        const idCliente = window.crypto?.randomUUID
            ? window.crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
        try {
            socket.send(JSON.stringify({
                tipo: "mensaje",
                contenido,
                id_cliente: idCliente,
            }));
        } catch {
            mostrarError("No se pudo enviar el mensaje. Inténtalo de nuevo.");
            return;
        }

        pendientes.set(idCliente, contenido);
        temporizadoresPendientes.set(idCliente, setTimeout(() => {
            if (!pendientes.has(idCliente)) return;
            temporizadoresPendientes.delete(idCliente);
            if (!campo.value.trim()) {
                campo.value = pendientes.get(idCliente);
                actualizarContador();
            }
            mostrarError("No se confirmó el envío. Revisa tu conexión y vuelve a intentarlo.");
        }, 10000));
        campo.value = "";
        actualizarContador();
        mostrarError();
    });

    campo?.addEventListener("input", () => {
        actualizarContador();
        mostrarError();
    });

    campo?.addEventListener("keydown", (evento) => {
        if (
            evento.key === "Enter"
            && !evento.shiftKey
            && !evento.isComposing
        ) {
            evento.preventDefault();
            formulario.requestSubmit();
        }
    });

    entradaArchivo?.addEventListener("change", () => {
        const archivo = entradaArchivo.files?.[0];
        if (archivo) prepararVistaAdjunto(archivo);
    });

    botonQuitarAdjunto?.addEventListener("click", limpiarAdjunto);

    botonGrabar?.addEventListener("click", async () => {
        if (grabadora && grabadora.state === "recording") {
            botonGrabar.disabled = true;
            grabadora.stop();
            return;
        }
        if (solicitandoMicrofono) return;
        if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
            mostrarError("Este navegador no permite grabar audio. Puedes adjuntar un archivo de audio.");
            return;
        }

        solicitandoMicrofono = true;
        botonGrabar.disabled = true;
        limpiarAdjunto();
        mostrarError();
        try {
            flujoAudio = await navigator.mediaDevices.getUserMedia({ audio: true });
            const tipos = [
                "audio/webm;codecs=opus",
                "audio/ogg;codecs=opus",
                "audio/mp4",
            ];
            const tipo = tipos.find((candidato) => MediaRecorder.isTypeSupported(candidato));
            grabadora = tipo
                ? new MediaRecorder(flujoAudio, { mimeType: tipo })
                : new MediaRecorder(flujoAudio);
            const partes = [];
            grabadora.addEventListener("dataavailable", (evento) => {
                if (evento.data.size) partes.push(evento.data);
            });
            grabadora.addEventListener("stop", () => {
                flujoAudio?.getTracks().forEach((pista) => pista.stop());
                flujoAudio = null;
                clearInterval(intervaloGrabacion);
                estadoGrabacion.hidden = true;
                botonGrabar.setAttribute("aria-label", "Grabar un audio");
                botonGrabar.title = "Grabar un audio";
                botonGrabar.dataset.grabando = "false";
                botonGrabar.disabled = false;
                const blob = new Blob(partes, { type: grabadora.mimeType || "audio/webm" });
                if (blob.size > 20 * 1024 * 1024) {
                    mostrarError("El audio no puede superar los 20 MB. Graba uno más corto.");
                    return;
                }
                if (!blob.size) {
                    mostrarError("No se capturó audio. Inténtalo de nuevo.");
                    return;
                }
                const extension = blob.type.includes("ogg")
                    ? "ogg"
                    : blob.type.includes("mp4")
                        ? "m4a"
                        : "webm";
                prepararVistaAdjunto(
                    new File([blob], `audio-${Date.now()}.${extension}`, { type: blob.type }),
                );
            });

            grabadora.start(250);
            solicitandoMicrofono = false;
            botonGrabar.disabled = false;
            botonGrabar.dataset.grabando = "true";
            inicioGrabacion = Date.now();
            estadoGrabacion.hidden = false;
            botonGrabar.setAttribute("aria-label", "Detener grabación");
            botonGrabar.title = "Detener grabación";
            intervaloGrabacion = setInterval(() => {
                const segundos = Math.floor((Date.now() - inicioGrabacion) / 1000);
                cronometro.textContent = `${String(Math.floor(segundos / 60)).padStart(2, "0")}:${String(segundos % 60).padStart(2, "0")}`;
            }, 250);
        } catch {
            solicitandoMicrofono = false;
            botonGrabar.disabled = false;
            botonGrabar.dataset.grabando = "false";
            flujoAudio?.getTracks().forEach((pista) => pista.stop());
            flujoAudio = null;
            mostrarError("No se pudo acceder al micrófono. Revisa los permisos del navegador.");
        }
    });

    botonCargarAnteriores?.addEventListener("click", cargarAnteriores);
    botonBajar?.addEventListener("click", () => {
        seguirAlFinal = true;
        mensajes.scrollTo({ top: mensajes.scrollHeight, behavior: "smooth" });
        botonBajar.hidden = true;
    });

    mensajes.addEventListener("load", mantenerChatAlFinal, true);
    mensajes.addEventListener("loadedmetadata", mantenerChatAlFinal, true);
    mensajes.addEventListener("scroll", () => {
        seguirAlFinal = (
            mensajes.scrollHeight - mensajes.scrollTop - mensajes.clientHeight < 80
        );
        if (seguirAlFinal) {
            botonBajar.hidden = true;
        }
    });

    actualizarContador();
    requestAnimationFrame(() => {
        mantenerChatAlFinal();
    });
    conectar();

    window.addEventListener("pagehide", () => {
        cerrarAlSalir = true;
        clearTimeout(reconexion);
        clearInterval(intervaloGrabacion);
        flujoAudio?.getTracks().forEach((pista) => pista.stop());
        if (socket && socket.readyState < WebSocket.CLOSING) socket.close();
        if (urlVistaPrevia) URL.revokeObjectURL(urlVistaPrevia);
        temporizadoresPendientes.forEach(clearTimeout);
    }, { once: true });
});
