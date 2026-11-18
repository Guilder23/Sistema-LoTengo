document.addEventListener("DOMContentLoaded", () => {
    const password = document.getElementById("id_password");
    const confirmation = document.getElementById("id_password_confirm");
    if (!password || !confirmation) return;

    const validateConfirmation = () => {
        confirmation.setCustomValidity(
            password.value === confirmation.value ? "" : "Las contraseñas no coinciden."
        );
    };

    password.addEventListener("input", validateConfirmation);
    confirmation.addEventListener("input", validateConfirmation);
});
