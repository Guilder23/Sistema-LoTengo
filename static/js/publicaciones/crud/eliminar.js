document.querySelector(".confirmacion-acciones")?.addEventListener("submit", (evento) => {
    const boton = evento.currentTarget.querySelector('button[type="submit"]');
    if (boton) {
        boton.disabled = true;
        boton.textContent = "Retirando publicación…";
    }
});
