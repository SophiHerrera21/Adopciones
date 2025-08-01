// Luna & Lía: Rescatando Huellas - JavaScript Principal

document.addEventListener('DOMContentLoaded', function() {
    // --- Preloader ---
    const preloader = document.getElementById('preloader');
    if (preloader) {
        // Espera a que toda la página (imágenes, etc.) se cargue
        window.addEventListener('load', () => {
            preloader.classList.add('fade-out');
            setTimeout(() => {
                preloader.style.display = 'none';
            }, 500); // Coincide con la duración de la transición en CSS
        });
    }

    // --- Inicializar Funcionalidades ---
    initAnimations();
    initFavoritos();
    initFiltros();
    initCarousel();

    // Lógica del botón "Scroll to Top"
    const scrollToTopBtn = document.getElementById('scrollToTopBtn');

    if (scrollToTopBtn) {
        // Mostrar/ocultar el botón basado en el scroll
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) { // Muestra el botón después de 300px de scroll
                scrollToTopBtn.style.display = 'block';
                scrollToTopBtn.style.opacity = '1';
            } else {
                scrollToTopBtn.style.opacity = '0';
                setTimeout(() => {
                    if(window.pageYOffset <= 300) {
                       scrollToTopBtn.style.display = 'none';
                    }
                }, 300); // Coincide con la transición
            }
        });

        // Acción de scroll al hacer clic
        scrollToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Activar tooltips de Bootstrap, si se usan
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Campos condicionales en pre-adopción
    const ninosEnCasaField = document.getElementById('id_ninos_en_casa');
    const edadesNinosField = document.getElementById('id_edades_ninos');
    const edadesNinosLabel = edadesNinosField ? edadesNinosField.previousElementSibling : null;
    const edadesNinosContainer = edadesNinosField ? edadesNinosField.parentElement : null;
    
    const tuvoMascotasField = document.getElementById('id_tuvo_mascotas');
    const experienciaMascotasField = document.getElementById('id_experiencia_mascotas');
    const experienciaMascotasLabel = experienciaMascotasField ? experienciaMascotasField.previousElementSibling : null;
    const experienciaMascotasContainer = experienciaMascotasField ? experienciaMascotasField.parentElement : null;
    
    const otrasMascotasField = document.getElementById('id_otras_mascotas');
    const otrasMascotasLabel = otrasMascotasField ? otrasMascotasField.previousElementSibling : null;
    const otrasMascotasContainer = otrasMascotasField ? otrasMascotasField.parentElement : null;
    
    const tieneVeterinarioField = document.getElementById('id_tiene_veterinario');
    const nombreVeterinarioField = document.getElementById('id_nombre_veterinario');
    const nombreVeterinarioLabel = nombreVeterinarioField ? nombreVeterinarioField.previousElementSibling : null;
    const nombreVeterinarioContainer = nombreVeterinarioField ? nombreVeterinarioField.parentElement : null;
    
    const tienePatioField = document.getElementById('id_tiene_patio');
    const tamanoPatioField = document.getElementById('id_tamano_patio');
    const tamanoPatioLabel = tamanoPatioField ? tamanoPatioField.previousElementSibling : null;
    const tamanoPatioContainer = tamanoPatioField ? tamanoPatioField.parentElement : null;
    
    // Función para mostrar/ocultar campos
    function toggleField(checkbox, field, label, container) {
        if (checkbox && field && container) {
            if (checkbox.checked) {
                container.style.display = 'block';
                if (label) label.style.display = 'block';
                field.required = true;
            } else {
                container.style.display = 'none';
                if (label) label.style.display = 'none';
                field.required = false;
                field.value = '';
            }
        }
    }
    
    // Función para manejar campo numérico de niños
    function toggleNinosField() {
        if (ninosEnCasaField && edadesNinosField && edadesNinosContainer) {
            const ninosCount = parseInt(ninosEnCasaField.value) || 0;
            if (ninosCount > 0) {
                edadesNinosContainer.style.display = 'block';
                if (edadesNinosLabel) edadesNinosLabel.style.display = 'block';
                edadesNinosField.required = true;
            } else {
                edadesNinosContainer.style.display = 'none';
                if (edadesNinosLabel) edadesNinosLabel.style.display = 'none';
                edadesNinosField.required = false;
                edadesNinosField.value = '';
            }
        }
    }
    
    // Event listeners para campos condicionales
    if (ninosEnCasaField) {
        ninosEnCasaField.addEventListener('change', toggleNinosField);
        toggleNinosField(); // Ejecutar al cargar la página
    }
    
    if (tuvoMascotasField) {
        tuvoMascotasField.addEventListener('change', function() {
            toggleField(this, experienciaMascotasField, experienciaMascotasLabel, experienciaMascotasContainer);
        });
        toggleField(tuvoMascotasField, experienciaMascotasField, experienciaMascotasLabel, experienciaMascotasContainer);
    }
    
    if (otrasMascotasField) {
        otrasMascotasField.addEventListener('change', function() {
            toggleField(this, otrasMascotasField, otrasMascotasLabel, otrasMascotasContainer);
        });
        toggleField(otrasMascotasField, otrasMascotasField, otrasMascotasLabel, otrasMascotasContainer);
    }
    
    if (tieneVeterinarioField) {
        tieneVeterinarioField.addEventListener('change', function() {
            toggleField(this, nombreVeterinarioField, nombreVeterinarioLabel, nombreVeterinarioContainer);
        });
        toggleField(tieneVeterinarioField, nombreVeterinarioField, nombreVeterinarioLabel, nombreVeterinarioContainer);
    }
    
    if (tienePatioField) {
        tienePatioField.addEventListener('change', function() {
            toggleField(this, tamanoPatioField, tamanoPatioLabel, tamanoPatioContainer);
        });
        toggleField(tienePatioField, tamanoPatioField, tamanoPatioLabel, tamanoPatioContainer);
    }
});

// Funcionalidad para raza dinámica en formulario de mascota
document.addEventListener('DOMContentLoaded', function() {
    const tipoField = document.getElementById('id_tipo');
    const razaField = document.getElementById('id_raza');
    
    if (tipoField && razaField) {
        const razasPerros = [
            ['', 'Selecciona una raza'],
            ['labrador', 'Labrador Retriever'],
            ['golden', 'Golden Retriever'],
            ['pastor_aleman', 'Pastor Alemán'],
            ['bulldog', 'Bulldog'],
            ['beagle', 'Beagle'],
            ['poodle', 'Poodle'],
            ['rottweiler', 'Rottweiler'],
            ['doberman', 'Doberman'],
            ['boxer', 'Boxer'],
            ['chihuahua', 'Chihuahua'],
            ['pug', 'Pug'],
            ['husky', 'Husky Siberiano'],
            ['criollo', 'Criollo'],
            ['otro', 'Otra raza']
        ];
        
        const razasGatos = [
            ['', 'Selecciona una raza'],
            ['siames', 'Siamés'],
            ['persa', 'Persa'],
            ['main_coon', 'Maine Coon'],
            ['bengala', 'Bengala'],
            ['ragdoll', 'Ragdoll'],
            ['british_shorthair', 'British Shorthair'],
            ['sphynx', 'Sphynx'],
            ['abyssinian', 'Abisinio'],
            ['russian_blue', 'Azul Ruso'],
            ['criollo', 'Criollo'],
            ['otro', 'Otra raza']
        ];
        
        function actualizarRazas() {
            const tipoSeleccionado = tipoField.value;
            razaField.innerHTML = '';
            
            let razas = [];
            if (tipoSeleccionado === 'perro') {
                razas = razasPerros;
            } else if (tipoSeleccionado === 'gato') {
                razas = razasGatos;
            } else {
                razas = [['', 'Primero selecciona el tipo de mascota']];
            }
            
            razas.forEach(function(raza) {
                const option = document.createElement('option');
                option.value = raza[0];
                option.textContent = raza[1];
                razaField.appendChild(option);
            });
        }
        
        tipoField.addEventListener('change', actualizarRazas);
        actualizarRazas(); // Ejecutar al cargar la página
    }
});

// Funcionalidad para campos condicionales en donación
document.addEventListener('DOMContentLoaded', function() {
    const tipoDonacionField = document.getElementById('id_tipo_donacion');
    
    if (tipoDonacionField) {
        function toggleCamposDonacion() {
            const tipoSeleccionado = tipoDonacionField.value;
            
            // Ocultar todos los campos específicos
            const camposMonetarios = document.querySelectorAll('.campo-monetario');
            const camposInsumos = document.querySelectorAll('.campo-insumo');
            const camposServicios = document.querySelectorAll('.campo-servicio');
            const camposEspecie = document.querySelectorAll('.campo-especie');
            
            camposMonetarios.forEach(campo => {
                campo.closest('.mb-3').style.display = 'none';
            });
            camposInsumos.forEach(campo => {
                campo.closest('.mb-3').style.display = 'none';
            });
            camposServicios.forEach(campo => {
                campo.closest('.mb-3').style.display = 'none';
            });
            camposEspecie.forEach(campo => {
                campo.closest('.mb-3').style.display = 'none';
            });
            
            // Mostrar campos según el tipo seleccionado
            if (tipoSeleccionado === 'monetaria') {
                camposMonetarios.forEach(campo => {
                    campo.closest('.mb-3').style.display = 'block';
                });
            } else if (tipoSeleccionado === 'insumos') {
                camposInsumos.forEach(campo => {
                    campo.closest('.mb-3').style.display = 'block';
                });
            } else if (tipoSeleccionado === 'servicios') {
                camposServicios.forEach(campo => {
                    campo.closest('.mb-3').style.display = 'block';
                });
            } else if (tipoSeleccionado === 'especie') {
                camposEspecie.forEach(campo => {
                    campo.closest('.mb-3').style.display = 'block';
                });
            }
        }
        
        tipoDonacionField.addEventListener('change', toggleCamposDonacion);
        toggleCamposDonacion(); // Ejecutar al cargar la página
    }
});

// Funcionalidad para notificaciones en tiempo real
document.addEventListener('DOMContentLoaded', function() {
    // Función para mostrar notificaciones sin recargar
    function mostrarNotificacion(mensaje, tipo = 'success') {
        const notificacion = document.createElement('div');
        notificacion.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
        notificacion.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notificacion.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notificacion);
        
        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            if (notificacion.parentNode) {
                notificacion.remove();
            }
        }, 5000);
    }
    
    // Función para actualizar contador de notificaciones
    function actualizarContadorNotificaciones() {
        fetch('/obtener-notificaciones-ajax/')
            .then(response => response.json())
            .then(data => {
                const contador = document.getElementById('notificaciones-contador');
                if (contador) {
                    contador.textContent = data.no_leidas;
                    contador.style.display = data.no_leidas > 0 ? 'inline' : 'none';
                }
            })
            .catch(error => console.error('Error al obtener notificaciones:', error));
    }
    
    // Interceptar envíos de formularios para mostrar notificaciones
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const formData = new FormData(form);
        
        // Solo interceptar formularios específicos
        if (form.action.includes('solicitar-adopcion') || 
            form.action.includes('donar') || 
            form.action.includes('agregar-mascota') ||
            form.action.includes('editar-mascota')) {
            
            e.preventDefault();
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarNotificacion(data.mensaje, 'success');
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1500);
                    }
                    // Actualizar contador de notificaciones
                    actualizarContadorNotificaciones();
                } else {
                    mostrarNotificacion(data.mensaje || 'Error en el formulario', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarNotificacion('Error al procesar la solicitud', 'danger');
            });
        }
    });
    
    // Actualizar contador de notificaciones cada 30 segundos
    setInterval(actualizarContadorNotificaciones, 30000);
    
    // Marcar notificaciones como leídas al hacer clic
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('marcar-leida')) {
            e.preventDefault();
            const notificacionId = e.target.dataset.notificacionId;
            
            fetch(`/marcar-notificacion-leida/${notificacionId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const notificacionElement = document.querySelector(`[data-notificacion-id="${notificacionId}"]`);
                    if (notificacionElement) {
                        notificacionElement.closest('.notificacion-item').remove();
                        actualizarContadorNotificaciones();
                    }
                }
            })
            .catch(error => console.error('Error al marcar notificación:', error));
        }
    });
});

// --- Animaciones Generales ---
function initAnimations() {
    const observerOptions = { threshold: 0.1 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });
}

// --- Sistema de Favoritos (AJAX) ---
function initFavoritos() {
    document.querySelectorAll('.btn-favorito, .btn-favorito-carousel').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const mascotaId = this.dataset.mascotaId;
            const esFavorito = this.dataset.esFavorito === 'true';
            const url = esFavorito ? `/mascota/${mascotaId}/quitar-favorito/` : `/mascota/${mascotaId}/agregar-favorito/`;

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.dataset.esFavorito = data.is_favorite ? 'true' : 'false';
                    this.innerHTML = data.is_favorite ? '❤️' : '🤍';
                    // Pequeña animación de "rebote"
                    this.style.transform = 'scale(1.2)';
                    setTimeout(() => { this.style.transform = 'scale(1)'; }, 200);
                }
            });
        });
    });
}

// --- Sistema de Filtros (Auto-submit) ---
function initFiltros() {
    const filtrosForm = document.getElementById('filtrosForm');
    if (filtrosForm) {
        filtrosForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', () => filtrosForm.submit());
        });
    }
}

// --- Carrusel ---
function initCarousel() {
    const carousel = document.getElementById('carouselMascotas');
    if (carousel) {
        // No se necesita JS extra si se usa data-bs-ride="carousel", Bootstrap lo maneja.
    }
}
