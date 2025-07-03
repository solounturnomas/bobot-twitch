document.addEventListener('DOMContentLoaded', () => {
    // Configuración inicial
    const grid = document.getElementById('grid');
    const currentCoords = document.getElementById('current-coords');
    let zoomLevel = 1;
    
    // Mapa de tipos de casillas a imágenes
    const TIPOS_CASILLAS = {
        'CESPED': 'cesped.png',
        'CAMPO': 'campo.png',
        'AGUA': 'agua.png',
        'MONTANA': 'montana.png',
        'CIUDADANO': 'ciudadano.png',
        'SOLAR': 'solar.png',
        'CAMINO': 'camino.png',
        'CAMINO_2': 'camino_2.png',
        'CRUCE': 'cruce.png',
        'CAMINO_GIRADO_1': 'camino_girado_1.png',
        'CAMINO_GIRADO_2': 'camino_girado_2.png',
        'CAMINO_GIRADO_3': 'camino_girado_3.png',
        'CAMINO_GIRADO_4': 'camino_girado_4.png',
        'POZO': 'pozo.png',
        'PUEBLO': 'pueblo.png',
    };

    // Mapa de niveles de casa
    const NIVELES_CASA = {
        0: 'nivel_casa_0.png',
        1: 'nivel_casa_1.png',
        2: 'nivel_casa_2.png',
        3: 'nivel_casa_3.png',
        4: 'nivel_casa_4.png'
    };

    // Función para actualizar la cuadrícula
    async function actualizarMapa() {
        try {
            const response = await fetch('/api/mapa');
            const casillas = await response.json();
            
            // Limpiar la cuadrícula actual
            grid.innerHTML = '';
            
            // Logs de depuración de datos
            console.log("Datos completos recibidos:", casillas);
            console.log("Estructura de la primera casilla:", casillas[0]);
            console.log("Número total de casillas:", casillas.length);
            
            // Calcular el rango del grid basado en los datos
            let maxAbsValue = 0;
            casillas.forEach(casilla => {
                const absX = Math.abs(casilla.x);
                const absZ = Math.abs(casilla.z);
                maxAbsValue = Math.max(maxAbsValue, absX, absZ);
            });
            
            // Asegurar un mínimo de 3 para que siempre haya al menos una plaza central
            const rango = Math.max(3, maxAbsValue);
            
            // Configurar el grid con el rango calculado
            grid.style.gridTemplateColumns = `repeat(${rango * 2 + 1}, 1fr)`;
            grid.style.gridTemplateRows = `repeat(${rango * 2 + 1}, 1fr)`;
            
            // Crear el grid con el rango calculado
            for (let x = -rango; x <= rango; x++) {
                for (let z = -rango; z <= rango; z++) {
                    const div = document.createElement('div');
                    div.classList.add('casilla');
                    div.dataset.x = x;
                    div.dataset.z = z;
                    
                    // Buscar la casilla en los datos obtenidos
                    const casilla = casillas.find(c => c.x === x && c.z === z);
                    if (casilla) {
                        
                        // Si es solar con ciudadano, mostramos doble fondo
                        if (casilla.ciudadano_id && casilla.tipo === 'SOLAR') {
                            console.log("¡Casilla cumple las condiciones! Mostrando doble fondo (solar y casa)");
                            console.log("Nivel de casa del ciudadano:", casilla.nivel_casa);
                            // Primero la casa del nivel del ciudadano
                            div.style.backgroundImage = `url('/static/img/casa/${NIVELES_CASA[casilla.nivel_casa] || 'nivel_casa_0.png'}')`;
                            // Luego el solar encima
                            div.style.backgroundImage += `, url('/static/img/casillas/${TIPOS_CASILLAS[casilla.tipo]}')`;
                            
                            // Si es una casa con ciudadano, agregar el tooltip
                            if (casilla.nombre) {
                                const tooltip = document.createElement('div');
                                tooltip.className = 'tooltip';
                                tooltip.textContent = `Casa de ${casilla.nombre}`;
                                div.appendChild(tooltip);
                            }
                            
                            // Si es la casilla (0,0) agregar tooltip de pozo
                            if (x === 0 && z === 0) {
                                const pozoTooltip = document.createElement('div');
                                pozoTooltip.className = 'tooltip';
                                pozoTooltip.textContent = 'Pozo';
                                div.appendChild(pozoTooltip);
                            }
                        } else {
                            console.log("Casilla no cumple las condiciones, mostrando imagen base");
                            const imagen = TIPOS_CASILLAS[casilla.tipo];
                            div.style.backgroundImage = `url('/static/img/casillas/${imagen}')`;
                        }                           
                    } else {
                        // Casilla vacía por defecto
                        div.style.backgroundColor = '#e0e0e0';
                    }
                    
                    // Añadir evento click
                    div.addEventListener('click', () => {
                        currentCoords.textContent = `${x},${z}`;
                    });
                    
                    grid.appendChild(div);
                }
            }
        } catch (error) {
            console.error('Error al actualizar la cuadrícula:', error);
        }
    }

    // Eventos de los botones
    document.getElementById('btn-zoom-in').addEventListener('click', () => {
        zoomLevel = Math.min(2, zoomLevel + 0.1);
        grid.style.transform = `scale(${zoomLevel})`;
    });

    document.getElementById('btn-zoom-out').addEventListener('click', () => {
        zoomLevel = Math.max(0.5, zoomLevel - 0.1);
        grid.style.transform = `scale(${zoomLevel})`;
    });

    document.getElementById('btn-center').addEventListener('click', () => {
        grid.style.transform = `scale(1)`;
        zoomLevel = 1;
    });

    // Actualizar la cuadrícula inicialmente
    actualizarMapa();

    // Actualizar cada 5 segundos
    setInterval(actualizarMapa, 20000);
});
