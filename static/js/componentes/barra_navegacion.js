document.addEventListener("DOMContentLoaded", () => {
    const navigation = document.getElementById("navegacionPrincipal");
    if (!navigation) return;

    navigation.addEventListener("click", (event) => {
        if (event.target.closest("a") && window.bootstrap && window.innerWidth < 992) {
            window.bootstrap.Collapse.getOrCreateInstance(navigation).hide();
        }
    });
});
