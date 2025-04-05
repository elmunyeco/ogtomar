// static/main/js/components/header.js
document.addEventListener('alpine:init', () => {
    Alpine.data('headerComponent', (initialActiveSection = '', initialBreadcrumbs = []) => ({
        activeSection: initialActiveSection,
        breadcrumbs: initialBreadcrumbs,
        isSubmenuOpen: false,
        hoveredItem: null,
        
        init() {
            // Determinar sección activa basada en la URL actual si no se especifica
            if (!this.activeSection) {
                const path = window.location.pathname;
                if (path.includes('/pacientes')) {
                    this.activeSection = 'pacientes';
                } else if (path.includes('/historias')) {
                    this.activeSection = 'historias';
                } else if (path.includes('/ordenes')) {
                    this.activeSection = 'ordenes';
                } else if (path === '/' || path === '/index.html') {
                    this.activeSection = 'inicio';
                }
            }
            
            // Breadcrumbs por defecto si no se especifican
            if (this.breadcrumbs.length === 0) {
                this.breadcrumbs = [
                    { label: 'Inicio', url: '/' }
                ];
                
                // Añadir breadcrumbs basados en la sección activa
                switch (this.activeSection) {
                    case 'pacientes':
                        this.breadcrumbs.push({ label: 'Pacientes', url: '/pacientes/' });
                        break;
                    case 'historias':
                        this.breadcrumbs.push({ label: 'Historias', url: '/historias/' });
                        break;
                    case 'ordenes':
                        this.breadcrumbs.push({ label: 'Órdenes', url: '/ordenes/' });
                        break;
                }
            }
        },
        
        // Método para manejar hover en los elementos del menú
        hoverMenuItem(item) {
            this.hoveredItem = item;
        },
        
        // Método para limpiar el hover
        clearHover() {
            this.hoveredItem = null;
        },
        
        // Método para cerrar sesión
        logout() {
            // En producción, esto redireccionaría a la URL de logout
            alert('Sesión cerrada');
            // Opcional: redireccionar después del logout
            // window.location.href = '/';
        },
        
        // Método para verificar si un elemento de menú está activo
        isActive(section) {
            return this.activeSection === section;
        },
        
        // Método para establecer breadcrumbs desde fuera del componente
        setBreadcrumbs(breadcrumbs) {
            this.breadcrumbs = breadcrumbs;
        },
        
        // Método para añadir un breadcrumb desde fuera del componente
        addBreadcrumb(label, url = null) {
            this.breadcrumbs.push({ label, url });
        }
    }));
});
