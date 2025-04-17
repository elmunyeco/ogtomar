// static/main/js/components/header.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando menú de navegación...');
    
    // Referencias a elementos del menú
    const menuToggles = document.querySelectorAll('.menu-toggle');
    const menuItems = document.querySelectorAll('.menu-item[data-menu]');
    const logoutButton = document.getElementById('logout-button');
    
    // Asegurarse de que todos los submenús estén ocultos al cargar
    menuItems.forEach(item => {
        const submenu = item.querySelector('.submenu-items');
        if (submenu) {
            submenu.classList.add('hidden');
        }
    });
    
    /**
     * Función para cerrar todos los submenús
     */
    function closeAllMenus() {
        menuItems.forEach(item => {
            const submenu = item.querySelector('.submenu-items');
            if (submenu) {
                submenu.classList.add('hidden');
            }
        });
    }
    
    /**
     * Manejador para clicks en los toggles de menú
     * Abre o cierra el submenú correspondiente
     */
    menuToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const menuItem = this.closest('.menu-item');
            const submenu = menuItem.querySelector('.submenu-items');
            
            if (!submenu.classList.contains('hidden')) {
                // Si ya está abierto, ciérralo
                submenu.classList.add('hidden');
            } else {
                // Cierra todos los menús y abre el seleccionado
                closeAllMenus();
                submenu.classList.remove('hidden');
            }
        });
    });
    
    /**
     * Cerrar menús al hacer clic fuera de ellos
     */
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.menu-item')) {
            closeAllMenus();
        }
    });
    
    /**
     * Permitir clics dentro de los submenús sin cerrarlos
     */
    const submenus = document.querySelectorAll('.submenu-items');
    submenus.forEach(submenu => {
        submenu.addEventListener('click', function(e) {
            // Si el clic fue en un enlace, permitir la navegación normal
            if (!e.target.closest('a')) {
                e.stopPropagation();
            }
        });
    });
    
    /**
     * Manejador para el botón de cerrar sesión
     */
    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            // Puedes personalizarlo según las necesidades de tu aplicación
            window.location.href = '/logout/';
        });
    }
    
    /**
     * Soporte para navegación con teclado para accesibilidad
     */
    menuToggles.forEach(toggle => {
        toggle.addEventListener('keydown', function(e) {
            // Presionar Enter o Espacio activa el menú
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
            
            // Presionar Escape cierra los menús
            if (e.key === 'Escape') {
                closeAllMenus();
            }
        });
    });
    
    console.log('Menú de navegación inicializado correctamente');
});
