document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-marketplace-municipality-picker]").forEach((picker) => {
        const department = picker.closest("form")?.querySelector('[name="departamento"]');
        const input = picker.querySelector("[data-marketplace-municipality-input]");
        const optionsList = picker.querySelector("[data-marketplace-municipality-options]");
        const status = picker.querySelector("[data-marketplace-municipality-status]");
        const endpoint = picker.dataset.municipiosUrl;

        if (!department || !input || !optionsList || !status || !endpoint) return;

        let municipalities = [];
        let activeIndex = -1;
        let requestId = 0;

        const normalize = (value) => value
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLocaleLowerCase();

        const closeOptions = () => {
            optionsList.hidden = true;
            optionsList.replaceChildren();
            input.setAttribute("aria-expanded", "false");
            input.removeAttribute("aria-activedescendant");
            activeIndex = -1;
        };

        const chooseMunicipality = (name) => {
            input.value = name;
            input.dispatchEvent(new Event("change", { bubbles: true }));
            closeOptions();
            status.textContent = `Municipio seleccionado: ${name}.`;
        };

        const setActiveOption = (index) => {
            const options = optionsList.querySelectorAll('[role="option"]');
            if (!options.length) return;

            activeIndex = (index + options.length) % options.length;
            options.forEach((option, optionIndex) => {
                const isActive = optionIndex === activeIndex;
                option.setAttribute("aria-selected", String(isActive));
                if (isActive) {
                    input.setAttribute("aria-activedescendant", option.id);
                    option.scrollIntoView({ block: "nearest" });
                }
            });
        };

        const showOptions = () => {
            if (!department.value || !municipalities.length) {
                closeOptions();
                status.textContent = department.value
                    ? "No hay municipios disponibles para este departamento."
                    : "Selecciona un departamento para ver sugerencias de municipios.";
                return;
            }

            const query = normalize(input.value.trim());
            const matches = municipalities
                .filter((name) => !query || normalize(name).includes(query));

            optionsList.replaceChildren();
            activeIndex = -1;
            input.removeAttribute("aria-activedescendant");

            matches.forEach((name, index) => {
                const option = document.createElement("li");
                option.id = `marketplace-municipality-option-${index}`;
                option.className = "marketplace-municipality-option";
                option.setAttribute("role", "option");
                option.setAttribute("aria-selected", "false");
                option.textContent = name;
                option.addEventListener("pointerdown", (event) => {
                    event.preventDefault();
                    chooseMunicipality(name);
                });
                optionsList.append(option);
            });

            optionsList.hidden = matches.length === 0;
            input.setAttribute("aria-expanded", String(matches.length > 0));
            status.textContent = matches.length
                ? `${matches.length} municipio${matches.length === 1 ? "" : "s"} disponible${matches.length === 1 ? "" : "s"}.`
                : "No hay municipios que coincidan con la búsqueda.";
        };

        const loadMunicipalities = async () => {
            const departmentCode = department.value;
            const currentRequest = ++requestId;
            municipalities = [];
            closeOptions();

            if (!departmentCode) {
                status.textContent = "Selecciona un departamento para ver sugerencias de municipios.";
                return;
            }

            status.textContent = "Cargando municipios...";
            try {
                const response = await fetch(
                    `${endpoint}?departamento=${encodeURIComponent(departmentCode)}`,
                    { headers: { Accept: "application/json" } },
                );
                if (!response.ok) {
                    throw new Error(`La solicitud de municipios respondió ${response.status}.`);
                }

                const data = await response.json();
                if (!Array.isArray(data.municipios) || !data.municipios.every((name) => typeof name === "string")) {
                    throw new Error("La respuesta de municipios no tiene el formato esperado.");
                }
                if (currentRequest !== requestId || departmentCode !== department.value) return;

                municipalities = [...new Set(data.municipios)];
                status.textContent = municipalities.length
                    ? `${municipalities.length} municipios disponibles.`
                    : "No hay municipios disponibles para este departamento.";
                if (document.activeElement === input) showOptions();
            } catch (error) {
                if (currentRequest !== requestId) return;
                console.error("No se pudieron cargar los municipios del filtro de ubicación.", error);
                status.textContent = "No se pudieron cargar los municipios. Intenta de nuevo.";
            }
        };

        department.addEventListener("change", async () => {
            const previousMunicipality = input.value.trim();
            await loadMunicipalities();
            if (
                department.value
                && previousMunicipality
                && !municipalities.some((name) => normalize(name) === normalize(previousMunicipality))
            ) {
                input.value = "";
            }
            if (document.activeElement === input) showOptions();
        });

        input.addEventListener("focus", showOptions);
        input.addEventListener("input", showOptions);
        input.addEventListener("keydown", (event) => {
            const options = optionsList.querySelectorAll('[role="option"]');
            if (event.key === "ArrowDown" && options.length) {
                event.preventDefault();
                setActiveOption(activeIndex + 1);
            } else if (event.key === "ArrowUp" && options.length) {
                event.preventDefault();
                setActiveOption(activeIndex < 0 ? options.length - 1 : activeIndex - 1);
            } else if (event.key === "Enter" && activeIndex >= 0 && options[activeIndex]) {
                event.preventDefault();
                chooseMunicipality(options[activeIndex].textContent);
            } else if (event.key === "Escape" && !optionsList.hidden) {
                event.preventDefault();
                closeOptions();
            }
        });

        document.addEventListener("pointerdown", (event) => {
            if (!picker.contains(event.target)) closeOptions();
        });

        loadMunicipalities();
    });
});
