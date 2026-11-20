document.addEventListener("DOMContentLoaded", () => {
    const pagina = document.querySelector("[data-notificaciones-configuracion]");
    const boton = pagina?.querySelector("[data-push-boton]");
    const estado = pagina?.querySelector("[data-push-estado]");
    if (!pagina || !boton || !estado) return;

    const csrfToken = document.cookie
        .split("; ")
        .find((cookie) => cookie.startsWith("csrftoken="))
        ?.split("=")[1];
    let configuracionPush = null;
    let suscripcionActual = null;

    const actualizarBoton = () => {
        boton.textContent = suscripcionActual
            ? "Desactivar en este dispositivo"
            : "Activar en este dispositivo";
    };

    const enviarJson = async (url, datos) => {
        const respuesta = await fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken || "",
            },
            body: JSON.stringify(datos),
        });
        let resultado = {};
        try {
            resultado = await respuesta.json();
        } catch {
            resultado = {};
        }
        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo guardar la suscripción.");
        }
        return resultado;
    };

    const decodificarClave = (clave) => {
        const base64 = clave.replace(/-/g, "+").replace(/_/g, "/");
        const relleno = "=".repeat((4 - base64.length % 4) % 4);
        const bytes = atob(base64 + relleno);
        return Uint8Array.from(bytes, (caracter) => caracter.charCodeAt(0));
    };

    const sincronizarSuscripcion = async (suscripcion) => {
        await enviarJson(pagina.dataset.registroUrl, suscripcion.toJSON());
        suscripcionActual = suscripcion;
        actualizarBoton();
    };

    const cargarEstado = async () => {
        if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
            boton.disabled = true;
            estado.textContent = "Este navegador no admite notificaciones push.";
            return;
        }

        try {
            const respuesta = await fetch(pagina.dataset.configuracionUrl, {
                credentials: "same-origin",
                headers: { Accept: "application/json" },
            });
            if (!respuesta.ok) throw new Error("No se pudo consultar la configuración push.");
            configuracionPush = await respuesta.json();
            if (!configuracionPush.habilitado) {
                boton.disabled = true;
                estado.textContent = "Las notificaciones del navegador aún no están configuradas en el servidor.";
                return;
            }

            if (Notification.permission === "denied") {
                boton.disabled = true;
                estado.textContent = "Bloqueaste los avisos. Actívalos en los permisos del navegador.";
                return;
            }
            if (Notification.permission === "granted") {
                const registro = await navigator.serviceWorker.getRegistration("/");
                suscripcionActual = await registro?.pushManager.getSubscription();
                if (suscripcionActual) await sincronizarSuscripcion(suscripcionActual);
            }
            estado.textContent = suscripcionActual
                ? "Los avisos del navegador están activos en este dispositivo."
                : configuracionPush.dispositivos_activos
                    ? `Los avisos están activos en ${configuracionPush.dispositivos_activos} otro(s) dispositivo(s).`
                    : "Aún no están activados en este dispositivo.";
            actualizarBoton();
        } catch {
            boton.disabled = true;
            estado.textContent = "No se pudo comprobar la configuración de notificaciones.";
        }
    };

    boton.addEventListener("click", async () => {
        boton.disabled = true;
        try {
            if (suscripcionActual) {
                await enviarJson(pagina.dataset.eliminarUrl, {
                    endpoint: suscripcionActual.endpoint,
                });
                await suscripcionActual.unsubscribe();
                suscripcionActual = null;
                estado.textContent = "Los avisos se desactivaron en este dispositivo.";
                actualizarBoton();
                return;
            }

            if (Notification.permission !== "granted") {
                const permiso = await Notification.requestPermission();
                if (permiso !== "granted") {
                    estado.textContent = permiso === "denied"
                        ? "Bloqueaste los avisos. Actívalos en los permisos del navegador."
                        : "No se activaron los avisos.";
                    return;
                }
            }

            const registro = await navigator.serviceWorker.register(
                pagina.dataset.serviceWorkerUrl,
                { scope: "/" },
            );
            await navigator.serviceWorker.ready;
            suscripcionActual = await registro.pushManager.getSubscription();
            if (!suscripcionActual) {
                suscripcionActual = await registro.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: decodificarClave(configuracionPush.clave_publica),
                });
            }
            await sincronizarSuscripcion(suscripcionActual);
            estado.textContent = "Los avisos del navegador están activos en este dispositivo.";
        } catch (error) {
            estado.textContent = error.message || "No se pudo activar la notificación.";
            if (error.message && error.message.includes("asociado a otra cuenta")) {
                suscripcionActual = null;
            }
        } finally {
            boton.disabled = false;
            actualizarBoton();
        }
    });

    cargarEstado();
});
