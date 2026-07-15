document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        const message = form.getAttribute("data-confirm") || "Lanjutkan?";
        if (!window.confirm(message)) {
            event.preventDefault();
        }
    });
});
