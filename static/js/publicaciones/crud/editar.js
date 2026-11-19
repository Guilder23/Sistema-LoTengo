const selectorImagenes = document.querySelector("#imagenesPublicacion");
const vistaPreviaImagenes = document.querySelector("#vistaPreviaImagenes");

const selectorDepartamento = document.querySelector('select[name="departamento"]');
const selectorMunicipio = document.querySelector('select[name="municipio"]');

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

selectorImagenes?.addEventListener("change", () => {
    vistaPreviaImagenes.replaceChildren();
    Array.from(selectorImagenes.files || []).forEach((archivo) => {
        if (!archivo.type.startsWith("image/")) {
            return;
        }
        const imagen = document.createElement("img");
        imagen.alt = `Vista previa: ${archivo.name}`;
        imagen.src = URL.createObjectURL(archivo);
        imagen.addEventListener("load", () => URL.revokeObjectURL(imagen.src), { once: true });
        vistaPreviaImagenes.append(imagen);
    });
});
