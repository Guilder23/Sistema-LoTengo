document.addEventListener("DOMContentLoaded", () => {
    const nombre = document.querySelector("#id_nombre");
    const contador = document.querySelector("#contador-nombre");
    if (!nombre || !contador) return;
    const actualizar = () => {
        contador.textContent = nombre.value.length;
    };
    nombre.addEventListener("input", actualizar);
    actualizar();
});
