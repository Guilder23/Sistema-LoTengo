document.addEventListener("DOMContentLoaded", () => {
    const notificaciones = document.querySelector(".navbar-notificaciones");
    const botonNotificaciones = notificaciones?.querySelector(".navbar-notificaciones-boton");
    const panelNotificaciones = notificaciones?.querySelector(".navbar-notificaciones-panel");
    const contadorNotificaciones = panelNotificaciones?.querySelector("[data-notificaciones-contador]");
    const listaNotificaciones = panelNotificaciones?.querySelector("[data-notificaciones-lista]");
    const formularioLeidas = panelNotificaciones?.querySelector("[data-marcar-notificaciones-leidas]");
    const insigniaNotificaciones = notificaciones?.querySelector("[data-notificaciones-insignia]");
    const menuCuenta = document.querySelector(".navbar-cuenta-menu");
    const botonCuenta = menuCuenta?.querySelector("[data-navbar-cuenta-boton]");
    const panelCuenta = menuCuenta?.querySelector(".navbar-cuenta-panel");
    const navegacion = document.getElementById("navegacionPrincipal");
    const formularioCerrarSesion = document.querySelector("[data-cerrar-sesion-form]");
    const enlacesChats = [...document.querySelectorAll("[data-enlace-chats]")];
    const insigniasChats = [...document.querySelectorAll("[data-chat-insignia]")];
    const conteosChats = [...document.querySelectorAll("[data-chat-conteo]")];
    const presenciaLista = [
        ...document.querySelectorAll("[data-presencia-usuario-id]"),
    ];
    const puntosPresencia = [
        ...document.querySelectorAll("[data-presencia-punto-usuario-id]"),
    ];
    const tiemposPresencia = new Map();
    let socketContadores = null;
    let reconexionContadores = null;
    let intervaloLatidoContadores = null;
    let intervaloTiemposPresencia = null;
    let esperaReconexionContadores = 1000;
    let cerrarContadores = false;

    const formatearTiempoPresencia = (segundos) => {
        const total = Math.floor(Math.max(0, segundos));
        if (total < 60) return `${total} s`;

        const minutos = Math.floor(total / 60);
        if (minutos < 60) return `${minutos} min`;

        const horas = Math.floor(minutos / 60);
        if (horas < 24) return `${horas} h`;

        const dias = Math.floor(horas / 24);
        if (dias < 30) return `${dias} d`;

        const meses = Math.floor(dias / 30);
        if (meses < 12) return `${meses} mes`;
        return `${Math.floor(dias / 365)} a`;
    };

    const actualizarTiempoPresencia = (elemento) => {
        const presencia = tiemposPresencia.get(elemento);
        if (!presencia) return;

        const segundos = presencia.segundos
            + (performance.now() - presencia.recibidaEn) / 1000;
        const tiempo = formatearTiempoPresencia(segundos);
        elemento.textContent = tiempo;
        elemento.title = `Desconectado hace ${tiempo}`;
        elemento.setAttribute("aria-label", `Desconectado hace ${tiempo}`);
    };

    const actualizarTiemposPresencia = () => {
        tiemposPresencia.forEach((_, elemento) => {
            if (!elemento.isConnected) {
                tiemposPresencia.delete(elemento);
                return;
            }
            actualizarTiempoPresencia(elemento);
        });
    };

    const actualizarPresenciaLista = (datos) => {
        const usuarioId = String(datos.usuario_id);
        const elementos = presenciaLista.filter(
            (elemento) => elemento.dataset.presenciaUsuarioId === usuarioId,
        );
        const puntos = puntosPresencia.filter(
            (elemento) => elemento.dataset.presenciaPuntoUsuarioId === usuarioId,
        );
        if (!elementos.length && !puntos.length) return;

        const enLinea = Boolean(datos.en_linea);
        const segundosDesconectado = Number.isFinite(
            datos.segundos_desde_ultima_vez,
        )
            ? Math.max(0, datos.segundos_desde_ultima_vez)
            : null;
        const recibidaEn = performance.now();

        puntos.forEach((punto) => {
            punto.hidden = !enLinea;
        });
        elementos.forEach((elemento) => {
            if (enLinea) {
                elemento.hidden = true;
                elemento.textContent = "";
                elemento.removeAttribute("title");
                elemento.removeAttribute("aria-label");
                delete elemento.dataset.estado;
                tiemposPresencia.delete(elemento);
            } else if (segundosDesconectado !== null) {
                elemento.hidden = false;
                elemento.dataset.estado = "desconectada";
                tiemposPresencia.set(elemento, {
                    segundos: segundosDesconectado,
                    recibidaEn,
                });
                actualizarTiempoPresencia(elemento);
            } else {
                elemento.hidden = true;
                elemento.textContent = "";
                elemento.removeAttribute("title");
                elemento.removeAttribute("aria-label");
                tiemposPresencia.delete(elemento);
            }
        });
    };

    const cerrarNotificaciones = () => {
        botonNotificaciones?.setAttribute("aria-expanded", "false");
        if (panelNotificaciones) panelNotificaciones.hidden = true;
    };

    const cerrarCuenta = () => {
        botonCuenta?.setAttribute("aria-expanded", "false");
        if (panelCuenta) panelCuenta.hidden = true;
    };

    const cerrarNavegacionMovil = () => {
        if (
            navegacion?.classList.contains("show")
            && window.innerWidth < 992
            && window.bootstrap
        ) {
            window.bootstrap.Collapse.getOrCreateInstance(navegacion).hide();
        }
    };

    const actualizarContadorChats = (cantidad, mensajesPorConversacion) => {
        const total = Number(cantidad) || 0;
        const etiqueta = total > 99 ? "99+" : String(total);
        insigniasChats.forEach((insignia) => {
            insignia.hidden = total === 0;
            insignia.textContent = etiqueta;
        });
        conteosChats.forEach((contador) => {
            contador.hidden = total === 0;
            contador.textContent = etiqueta;
            contador.setAttribute(
                "aria-label",
                total ? `${total} chats con mensajes sin leer` : "Sin chats sin leer",
            );
        });
        if (mensajesPorConversacion) {
            document.querySelectorAll("[data-conversacion]").forEach((conversacion) => {
                const cantidadConversacion = Number(
                    mensajesPorConversacion[conversacion.dataset.conversacionId],
                ) || 0;
                const insignia = conversacion.querySelector("[data-conversacion-conteo]");
                if (!insignia) return;

                insignia.hidden = cantidadConversacion === 0;
                insignia.textContent = cantidadConversacion > 99
                    ? "99+"
                    : String(cantidadConversacion);
                insignia.setAttribute(
                    "aria-label",
                    cantidadConversacion
                        ? `${cantidadConversacion} mensajes sin leer`
                        : "Sin mensajes sin leer",
                );
                conversacion.dataset.noLeidos = String(cantidadConversacion > 0);
            });
            document.dispatchEvent(new Event("chat-contadores-actualizados"));
        }
        enlacesChats.forEach((enlace) => {
            if (enlace.classList.contains("navbar-action-messages")) {
                enlace.setAttribute(
                    "aria-label",
                    total ? `Abrir conversaciones, ${total} mensajes sin leer` : "Abrir conversaciones",
                );
            }
        });
    };

    const actualizarContadorNotificaciones = (cantidad) => {
        const total = Number(cantidad) || 0;
        if (contadorNotificaciones) {
            contadorNotificaciones.textContent = `${total} sin leer`;
        }
        if (botonNotificaciones) {
            botonNotificaciones.setAttribute(
                "aria-label",
                total ? `Abrir notificaciones, ${total} sin leer` : "Abrir notificaciones",
            );
        }
        if (insigniaNotificaciones) {
            insigniaNotificaciones.hidden = total === 0;
            insigniaNotificaciones.textContent = total > 99 ? "99+" : String(total);
        }
    };

    const cargarNotificaciones = async () => {
        if (!panelNotificaciones?.dataset.resumenUrl || !listaNotificaciones) return;

        try {
            const respuesta = await fetch(panelNotificaciones.dataset.resumenUrl, {
                credentials: "same-origin",
                headers: { Accept: "application/json" },
            });
            if (!respuesta.ok) throw new Error("No se pudieron cargar las notificaciones.");

            const datos = await respuesta.json();
            actualizarContadorChats(
                datos.chats_sin_leer,
                datos.mensajes_por_conversacion,
            );
            actualizarContadorNotificaciones(datos.sin_leer);

            listaNotificaciones.replaceChildren();
            if (!datos.notificaciones.length) {
                const vacio = document.createElement("li");
                vacio.className = "navbar-notificaciones-vacia";
                vacio.textContent = "Todavía no tienes notificaciones.";
                listaNotificaciones.append(vacio);
                return;
            }

            datos.notificaciones.forEach((notificacion) => {
                const elemento = document.createElement("li");
                const enlace = document.createElement("a");
                const titulo = document.createElement("strong");
                const mensaje = document.createElement("span");

                elemento.className = notificacion.leida
                    ? "navbar-notificacion"
                    : "navbar-notificacion navbar-notificacion-no-leida";
                enlace.href = notificacion.url;
                titulo.textContent = notificacion.titulo;
                mensaje.textContent = notificacion.mensaje;
                enlace.append(titulo, mensaje);
                elemento.append(enlace);
                listaNotificaciones.append(elemento);
            });
        } catch {
            listaNotificaciones.replaceChildren();
            const error = document.createElement("li");
            error.className = "navbar-notificaciones-vacia";
            error.textContent = "No se pudieron cargar las notificaciones.";
            listaNotificaciones.append(error);
        }
    };

    const conectarContadores = () => {
        if (cerrarContadores) return;

        const url = new URL("/ws/notificaciones/", window.location.href);
        url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        socketContadores = new WebSocket(url);
        socketContadores.addEventListener("open", () => {
            esperaReconexionContadores = 1000;
            clearInterval(intervaloLatidoContadores);
            intervaloLatidoContadores = window.setInterval(() => {
                if (socketContadores?.readyState !== WebSocket.OPEN) return;
                try {
                    socketContadores.send(JSON.stringify({ tipo: "ping" }));
                } catch (error) {
                    console.error("No se pudo mantener activa la presencia.", error);
                }
            }, 25000);
            const usuarios = [
                ...new Set(
                    presenciaLista
                        .map((elemento) => elemento.dataset.presenciaUsuarioId)
                        .filter(Boolean),
                ),
            ];
            if (usuarios.length) {
                try {
                    socketContadores.send(
                        JSON.stringify({
                            tipo: "presencia_suscribir",
                            usuarios,
                        }),
                    );
                } catch (error) {
                    console.error(
                        "No se pudo solicitar la presencia de los chats.",
                        error,
                    );
                }
            }
        });
        socketContadores.addEventListener("message", (evento) => {
            let datos;
            try {
                datos = JSON.parse(evento.data);
            } catch (error) {
                console.error("El servidor envió un contador en formato inválido.", error);
                return;
            }
            if (datos.tipo === "presencia") {
                actualizarPresenciaLista(datos);
                return;
            }
            if (datos.tipo !== "contadores") return;

            actualizarContadorChats(
                datos.chats_sin_leer,
                datos.mensajes_por_conversacion,
            );
            actualizarContadorNotificaciones(datos.notificaciones_sin_leer);
            if (panelNotificaciones && !panelNotificaciones.hidden) {
                cargarNotificaciones();
            }
        });
        socketContadores.addEventListener("error", () => {
            socketContadores?.close();
        });
        socketContadores.addEventListener("close", () => {
            clearInterval(intervaloLatidoContadores);
            socketContadores = null;
            if (cerrarContadores) return;
            reconexionContadores = window.setTimeout(
                conectarContadores,
                esperaReconexionContadores,
            );
            esperaReconexionContadores = Math.min(
                esperaReconexionContadores * 2,
                30000,
            );
        });
    };

    botonNotificaciones?.addEventListener("click", () => {
        const abierto = botonNotificaciones.getAttribute("aria-expanded") === "true";
        cerrarCuenta();
        cerrarNavegacionMovil();
        botonNotificaciones.setAttribute("aria-expanded", String(!abierto));
        if (panelNotificaciones) panelNotificaciones.hidden = abierto;
        if (!abierto) cargarNotificaciones();
    });

    botonCuenta?.addEventListener("click", () => {
        const abierto = botonCuenta.getAttribute("aria-expanded") === "true";
        cerrarNotificaciones();
        cerrarNavegacionMovil();
        botonCuenta.setAttribute("aria-expanded", String(!abierto));
        if (panelCuenta) panelCuenta.hidden = abierto;
    });

    formularioCerrarSesion?.addEventListener("submit", (evento) => {
        if (formularioCerrarSesion.dataset.procesando === "true") {
            evento.preventDefault();
            return;
        }
        evento.preventDefault();
        formularioCerrarSesion.dataset.procesando = "true";

        const prepararCierre = async () => {
            try {
                if ("serviceWorker" in navigator) {
                    const registro = await navigator.serviceWorker.getRegistration();
                    const suscripcion = await registro?.pushManager.getSubscription();
                    const campo = formularioCerrarSesion.querySelector("[data-push-endpoint]");
                    if (campo && suscripcion) campo.value = suscripcion.endpoint;
                }
            } catch (error) {
                console.error("No se pudo consultar la suscripción push al cerrar sesión.", error);
            }
            HTMLFormElement.prototype.submit.call(formularioCerrarSesion);
        };

        prepararCierre();
    });

    document.addEventListener("click", (evento) => {
        if (notificaciones && !notificaciones.contains(evento.target)) {
            cerrarNotificaciones();
        }
        if (menuCuenta && !menuCuenta.contains(evento.target)) {
            cerrarCuenta();
        }
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key !== "Escape") return;

        if (botonCuenta?.getAttribute("aria-expanded") === "true") {
            cerrarCuenta();
            botonCuenta.focus();
        } else if (botonNotificaciones?.getAttribute("aria-expanded") === "true") {
            cerrarNotificaciones();
            botonNotificaciones.focus();
        }
    });

    formularioLeidas?.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const boton = formularioLeidas.querySelector("button");
        if (boton) boton.disabled = true;
        try {
            const respuesta = await fetch(formularioLeidas.action, {
                method: "POST",
                body: new FormData(formularioLeidas),
                credentials: "same-origin",
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!respuesta.ok) throw new Error("No se pudieron actualizar las notificaciones.");
            await cargarNotificaciones();
        } catch {
            if (contadorNotificaciones) {
                contadorNotificaciones.textContent = "No se pudo actualizar";
            }
        } finally {
            if (boton) boton.disabled = false;
        }
    });

    cargarNotificaciones();
    const intervaloNotificaciones = window.setInterval(cargarNotificaciones, 45000);
    if (presenciaLista.length) {
        intervaloTiemposPresencia = window.setInterval(
            actualizarTiemposPresencia,
            15000,
        );
    }
    conectarContadores();
    window.addEventListener("pagehide", () => {
        cerrarContadores = true;
        window.clearTimeout(reconexionContadores);
        window.clearInterval(intervaloLatidoContadores);
        window.clearInterval(intervaloTiemposPresencia);
        window.clearInterval(intervaloNotificaciones);
        socketContadores?.close();
    }, { once: true });
});
