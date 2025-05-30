// Archivo: ecocardiograma/static/ecocardiograma/js/segmentos-cardiacos.js

/**
 * Clase para manejar la visualización y manipulación de segmentos cardíacos
 * en estudios de ecocardiograma
 */
class SegmentosCardiacos {
    constructor(containerRef, canvasRef, imagenRef) {
        this.container = containerRef;
        this.canvas = canvasRef;
        this.imagen = imagenRef;
        this.ctx = null;
        this.escala = 1;
        this.imagenCargada = false;
        
        // Estados y colores de los segmentos
        this.estados = {
            '0': { nombre: 'No evaluado', color: '#FFFFFF' },
            '1': { nombre: 'Normal', color: '#FFFF00' },
            '2': { nombre: 'Hipoquinético', color: '#FF7700' },
            '3': { nombre: 'Aquinético', color: '#FF0000' },
            '4': { nombre: 'Disquinético', color: '#0000FF' }
        };
        
        // Coordenadas de los polígonos de segmentos (normalizadas a la imagen original)
        this.coordenadas = {
            1: [[66,62,67,76,86,75,112,76,113,62,66,62]],
            2: [
                [13,70,15,85,33,81,51,78,66,77,65,62,48,62,32,66,13,70],
                [254,64,263,80,269,77,278,76,287,76,294,78,299,80,309,64,301,59,292,58,281,56,275,57,266,58,259,61,254,64]
            ],
            3: [[426,75,425,109,439,112,441,75,426,75]],
            4: [
                [225,112,244,112,245,105,247,98,248,94,253,89,257,85,262,80,253,64,247,68,236,79,230,89,226,102,225,112],
                [427,43,426,75,442,75,443,43,443,43]
            ],
            5: [[427,16,427,43,443,43,444,34,446,27,452,20,457,19,457,7,447,8,439,10,427,16]],
            6: [[581,86,581,102,585,125,600,122,600,113,600,98,600,86,581,86]],
            7: [
                [225,112,225,120,230,136,235,145,240,151,248,158,253,161,263,144,261,142,263,136,263,132,258,131,248,131,246,123,245,117,244,112,225,112],
                [581,85,600,85,600,76,603,60,604,52,588,41,585,53,582,65,582,74,582,85]
            ],
            8: [[588,40,604,53,609,40,615,32,620,30,620,13,611,14,603,18,595,27,591,34,588,40]],
            9: [[62,138,57,153,100,162,104,146,86,125,82,123,79,124,78,128,87,136,87,140,79,140,62,138]],
            10: [
                [26,120,21,138,57,153,61,136,46,132,46,130,64,126,67,124,66,122,57,120,26,120],
                [262,144,253,160,260,165,266,167,274,168,288,169,295,167,301,165,309,161,299,145,292,148,287,149,275,148,267,146,262,144]
            ],
            11: [[497,75,497,89,497,103,497,115,512,119,518,97,518,84,515,72,497,75]],
            12: [
                [318,113,318,118,316,124,313,131,304,131,300,131,299,133,299,138,300,144,310,161,317,156,325,147,331,139,334,131,336,122,337,112,318,113],
                [483,42,492,64,496,75,514,72,507,53,497,34,483,42]
            ],
            13: [[457,20,463,21,467,23,478,34,483,42,497,34,488,22,476,13,465,8,457,7,457,20]],
            14: [[655,91,655,100,655,114,654,123,651,129,668,134,676,125,676,102,674,87,655,91]],
            15: [
                [299,80,306,85,310,90,314,95,317,102,318,106,318,113,337,113,337,103,334,93,330,84,325,77,317,69,309,64,299,80],
                [645,56,649,68,653,81,655,91,674,88,671,70,665,52,661,45,645,56]
            ],
            16: [[620,13,620,31,629,33,640,45,645,56,662,45,654,34,642,21,632,16,624,14,620,13]]
        };
        
        // Descripción de cada segmento
        this.descripciones = {
            1: 'Septum Anterior Basal - LAD',
            2: 'Septum Anterior Medio - LAD',
            3: 'Septum Basal - RAD',
            4: 'Septum Medio - RAD',
            5: 'Septum Aplical - LAD',
            6: 'Inferior Basal - RAD',
            7: 'Inferior Medio - RAD',
            8: 'Inferior Aplical - LAD',
            9: 'Posterior Basal - CRX',
            10: 'Posterior Medio - CRX',
            11: 'Lateral Basal - CRX',
            12: 'Lateral Medio - CRX',
            13: 'Lateral Aplical - LAD',
            14: 'Anterior Basal - LAD',
            15: 'Anterior Medio - LAD',
            16: 'Anterior Aplical - LAD'
        };
        
        // Valores actuales de los segmentos
        this.valoresSegmentos = {};
        
        // Inicializar
        this.inicializar();
    }
    
    /**
     * Inicializa el componente
     */
    inicializar() {
        if (this.imagen) {
            if (this.imagen.complete) {
                this.configurarCanvas();
            } else {
                this.imagen.addEventListener('load', () => {
                    this.configurarCanvas();
                });
            }
        }
        
        // Inicializar valores por defecto
        for (let i = 1; i <= 16; i++) {
            this.valoresSegmentos[i] = '0';
        }
    }
    
    /**
     * Configura el canvas para dibujar sobre la imagen
     */
    configurarCanvas() {
        if (!this.canvas || !this.imagen) return;
        
        // Obtener las dimensiones reales de la imagen
        const rectImagen = this.imagen.getBoundingClientRect();
        
        // Configurar el canvas
        this.canvas.width = this.imagen.naturalWidth;
        this.canvas.height = this.imagen.naturalHeight;
        this.canvas.style.width = rectImagen.width + 'px';
        this.canvas.style.height = rectImagen.height + 'px';
        
        // Calcular la escala
        this.escala = this.imagen.naturalWidth / rectImagen.width;
        
        // Obtener contexto
        this.ctx = this.canvas.getContext('2d');
        this.imagenCargada = true;
        
        // Dibujar segmentos iniciales
        this.dibujarTodosLosSegmentos();
    }
    
    /**
     * Establece el valor de un segmento específico
     */
    establecerSegmento(numero, estado) {
        if (numero >= 1 && numero <= 16 && this.estados[estado]) {
            this.valoresSegmentos[numero] = estado;
            this.dibujarTodosLosSegmentos();
        }
    }
    
    /**
     * Obtiene el valor de un segmento
     */
    obtenerSegmento(numero) {
        return this.valoresSegmentos[numero] || '0';
    }
    
    /**
     * Establece todos los segmentos con el mismo valor
     */
    establecerTodos(estado) {
        if (this.estados[estado]) {
            for (let i = 1; i <= 16; i++) {
                this.valoresSegmentos[i] = estado;
            }
            this.dibujarTodosLosSegmentos();
        }
    }
    
    /**
     * Carga valores desde un objeto
     */
    cargarValores(valores) {
        Object.assign(this.valoresSegmentos, valores);
        this.dibujarTodosLosSegmentos();
    }
    
    /**
     * Obtiene todos los valores actuales
     */
    obtenerValores() {
        return { ...this.valoresSegmentos };
    }
    
    /**
     * Dibuja todos los segmentos en el canvas
     */
    dibujarTodosLosSegmentos() {
        if (!this.ctx || !this.imagenCargada) return;
        
        // Limpiar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Dibujar cada segmento
        for (let numero = 1; numero <= 16; numero++) {
            const estado = this.valoresSegmentos[numero] || '0';
            this.dibujarSegmento(numero, estado);
        }
    }
    
    /**
     * Dibuja un segmento específico
     */
    dibujarSegmento(numero, estado) {
        if (!this.ctx || !this.coordenadas[numero] || estado === '0') return;
        
        const configuracionEstado = this.estados[estado];
        if (!configuracionEstado) return;
        
        // Configurar estilo
        this.ctx.fillStyle = configuracionEstado.color;
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 1;
        this.ctx.globalAlpha = 0.6;
        
        // Dibujar todos los polígonos para este segmento
        this.coordenadas[numero].forEach(coordenadas => {
            this.ctx.beginPath();
            this.ctx.moveTo(coordenadas[0], coordenadas[1]);
            
            for (let i = 2; i < coordenadas.length; i += 2) {
                this.ctx.lineTo(coordenadas[i], coordenadas[i + 1]);
            }
            
            this.ctx.closePath();
            this.ctx.fill();
            this.ctx.stroke();
        });
        
        this.ctx.globalAlpha = 1;
    }
    
    /**
     * Obtiene el área clicable para un segmento (para eventos de click)
     */
    obtenerAreaClicable(numero) {
        const coordenadas = this.coordenadas[numero];
        if (!coordenadas || !coordenadas[0]) return null;
        
        // Calcular bounding box del primer polígono
        const coords = coordenadas[0];
        let minX = coords[0], maxX = coords[0];
        let minY = coords[1], maxY = coords[1];
        
        for (let i = 2; i < coords.length; i += 2) {
            minX = Math.min(minX, coords[i]);
            maxX = Math.max(maxX, coords[i]);
            minY = Math.min(minY, coords[i + 1]);
            maxY = Math.max(maxY, coords[i + 1]);
        }
        
        // Convertir a porcentajes relativos a la imagen
        const width = this.imagen.naturalWidth;
        const height = this.imagen.naturalHeight;
        
        return {
            left: (minX / width * 100).toFixed(1),
            top: (minY / height * 100).toFixed(1),
            width: ((maxX - minX) / width * 100).toFixed(1),
            height: ((maxY - minY) / height * 100).toFixed(1)
        };
    }
    
    /**
     * Redimensiona el canvas cuando cambia el tamaño de la imagen
     */
    redimensionar() {
        if (this.imagenCargada) {
            this.configurarCanvas();
        }
    }
    
    /**
     * Exporta los datos de segmentos para guardado
     */
    exportarDatos() {
        const datos = {};
        for (let i = 1; i <= 16; i++) {
            const valor = this.valoresSegmentos[i];
            if (valor && valor !== '0') {
                datos[i] = parseInt(valor);
            }
        }
        return datos;
    }
    
    /**
     * Valida que un punto esté dentro de un polígono
     */
    puntoEnPoligono(x, y, coordenadas) {
        let dentro = false;
        const numPuntos = coordenadas.length / 2;
        
        for (let i = 0, j = numPuntos - 1; i < numPuntos; j = i++) {
            const xi = coordenadas[i * 2];
            const yi = coordenadas[i * 2 + 1];
            const xj = coordenadas[j * 2];
            const yj = coordenadas[j * 2 + 1];
            
            if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
                dentro = !dentro;
            }
        }
        
        return dentro;
    }
    
    /**
     * Obtiene el segmento en una posición específica
     */
    obtenerSegmentoEnPosicion(x, y) {
        // Convertir coordenadas de pantalla a coordenadas de imagen
        const rect = this.imagen.getBoundingClientRect();
        const xImg = (x - rect.left) * this.escala;
        const yImg = (y - rect.top) * this.escala;
        
        // Buscar en qué segmento está el punto
        for (let numero = 1; numero <= 16; numero++) {
            const coordenadas = this.coordenadas[numero];
            if (coordenadas) {
                for (const poligono of coordenadas) {
                    if (this.puntoEnPoligono(xImg, yImg, poligono)) {
                        return numero;
                    }
                }
            }
        }
        
        return null;
    }
}

// Hacer disponible globalmente
window.SegmentosCardiacos = SegmentosCardiacos;