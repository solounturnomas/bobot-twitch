/**
 * Funciones para la gestión de acciones del ciudadano
 */

/**
 * Función para ejecutar una acción del juego
 * @param {string} codigoAccion - Código de la acción a ejecutar
 * @param {string} nombreCiudadano - Nombre del ciudadano que realiza la acción
 */
function ejecutarAccion(codigoAccion, nombreCiudadano) {
    // Mostrar indicador de carga
    const ultimaAccionContainer = document.querySelector('.ultima-accion');
    const mensajeOriginal = ultimaAccionContainer.innerHTML;
    
    ultimaAccionContainer.innerHTML = `
        <div class="cargando">
            <i class="fas fa-spinner fa-spin"></i> Ejecutando acción ${codigoAccion}...
        </div>`;
    
    // Hacer la petición al servidor
    fetch('/ejecutar-accion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            codigo_accion: codigoAccion,
            nombre_ciudadano: nombreCiudadano
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Éxito
            ultimaAccionContainer.innerHTML = `
                <div class="accion-exitosa">
                    <i class="fas fa-check-circle"></i> ${data.mensaje}
                </div>`;
            
            // Recargar la página después de 1.5 segundos
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            // Error
            ultimaAccionContainer.innerHTML = `
                <div class="accion-error">
                    <i class="fas fa-exclamation-circle"></i> ${data.mensaje || 'Error al ejecutar la acción'}
                </div>`;
            
            // Restaurar el mensaje original después de 5 segundos
            setTimeout(() => {
                if (ultimaAccionContainer.innerHTML.includes('Error al ejecutar')) {
                    ultimaAccionContainer.innerHTML = mensajeOriginal;
                }
            }, 5000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ultimaAccionContainer.innerHTML = `
            <div class="accion-error">
                <i class="fas fa-exclamation-triangle"></i> Error de conexión al ejecutar la acción
            </div>`;
        
        // Restaurar el mensaje original después de 5 segundos
        setTimeout(() => {
            if (ultimaAccionContainer.innerHTML.includes('Error de conexión')) {
                ultimaAccionContainer.innerHTML = mensajeOriginal;
            }
        }, 5000);
    });
}

/**
 * Función para fabricar un producto
 * @param {string} producto - Nombre del producto a fabricar
 * @param {HTMLElement} elemento - Elemento HTML que disparó el evento
 */
function fabricarProducto(producto, elemento) {
    // Mostrar indicador de carga
    const ultimaAccionContainer = document.querySelector('.ultima-accion');
    const mensajeOriginal = ultimaAccionContainer.innerHTML;
    const icono = elemento;
    const originalSrc = icono.src;
    
    // Cambiar el cursor y deshabilitar temporalmente
    icono.style.cursor = 'wait';
    
    // Mostrar mensaje de carga
    ultimaAccionContainer.innerHTML = `
        <div class="cargando">
            <i class="fas fa-spinner fa-spin"></i> Fabricando ${producto}...
        </div>`;
    
    // Hacer la petición al servidor
    fetch('/fabricar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ producto: producto })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Éxito
            ultimaAccionContainer.innerHTML = `
                <div class="accion-exitosa">
                    <i class="fas fa-check-circle"></i> ${data.message}
                </div>`;
            
            // Recargar la página después de 1.5 segundos
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            // Error
            ultimaAccionContainer.innerHTML = `
                <div class="accion-error">
                    <i class="fas fa-exclamation-circle"></i> ${data.message || 'Error al fabricar el producto'}
                </div>`;
            
            // Restaurar el icono
            setTimeout(() => {
                icono.src = originalSrc;
                icono.style.cursor = 'pointer';
            }, 100);
            
            // Restaurar el mensaje original después de 5 segundos
            setTimeout(() => {
                if (ultimaAccionContainer.innerHTML.includes('Error al fabricar')) {
                    ultimaAccionContainer.innerHTML = mensajeOriginal;
                }
            }, 5000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ultimaAccionContainer.innerHTML = `
            <div class="accion-error">
                <i class="fas fa-exclamation-triangle"></i> Error de conexión al intentar fabricar
            </div>`;
        
        // Restaurar el icono
        setTimeout(() => {
            icono.src = originalSrc;
            icono.style.cursor = 'pointer';
        }, 100);
        
        // Restaurar el mensaje original después de 5 segundos
        setTimeout(() => {
            if (ultimaAccionContainer.innerHTML.includes('Error de conexión')) {
                ultimaAccionContainer.innerHTML = mensajeOriginal;
            }
        }, 5000);
    });
}
