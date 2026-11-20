self.addEventListener("push", (evento) => {
    const datos = evento.data ? evento.data.json() : {};
    const url = typeof datos.url === "string" ? datos.url : "/";
    evento.waitUntil(
        self.registration.showNotification(datos.title || "Lotengo", {
            body: datos.body || "Tienes una novedad.",
            icon: "/static/favicon.svg",
            badge: "/static/favicon.svg",
            data: { url },
        }),
    );
});

self.addEventListener("notificationclick", (evento) => {
    evento.notification.close();
    const destino = new URL(evento.notification.data?.url || "/", self.location.origin);
    if (destino.origin !== self.location.origin) return;

    evento.waitUntil(
        self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientes) => {
            for (const cliente of clientes) {
                if (cliente.url.startsWith(self.location.origin) && "focus" in cliente) {
                    return cliente.navigate(destino.href).then(() => cliente.focus());
                }
            }
            return self.clients.openWindow(destino.href);
        }),
    );
});
