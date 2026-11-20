document.addEventListener("DOMContentLoaded", () => {
    const departamento = document.querySelector("#id_departamento");
    const nombre = document.querySelector("#id_nombre");
    const textoDepartamento = document.querySelector("#departamento-seleccionado");
    const contador = document.querySelector("#contador-nombre");
    if (nombre && contador) {
        const actualizarContador = () => {
            contador.textContent = nombre.value.length;
        };
        nombre.addEventListener("input", actualizarContador);
        actualizarContador();
    }
    if (departamento && textoDepartamento) {
        departamento.addEventListener("change", () => {
            const opcion = departamento.options[departamento.selectedIndex];
            textoDepartamento.textContent = opcion.value
                ? `Municipio asignado a ${opcion.text}.`
                : "Elige el departamento al que pertenece este municipio.";
        });
    }
});
