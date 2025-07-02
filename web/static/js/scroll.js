// Guardar la posición del scroll antes de recargar la página
window.addEventListener('beforeunload', function() {
    localStorage.setItem('scrollPosition', window.scrollY);
});

// Restaurar la posición del scroll al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const scrollPosition = localStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        // Limpiar el valor después de usarlo
        localStorage.removeItem('scrollPosition');
    }
});
