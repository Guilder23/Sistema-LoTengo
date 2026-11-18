document.addEventListener("DOMContentLoaded", () => {
    const email = document.getElementById("id_email");
    if (email) email.addEventListener("change", () => { email.value = email.value.trim(); });
});
