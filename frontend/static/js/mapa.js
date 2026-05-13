/* ============================================================
   U-RIDE — mapa.js
   Integración de Leaflet.js con OpenStreetMap
   Routing via OSRM (Open Source Routing Machine — GRATIS)
   ============================================================ */

window.URideMapa = (function () {
    'use strict';

    let _map = null;
    let _routeLayer = null;
    let _carMarker = null;
    let _simulationInterval = null;
    let _userMarker = null;
    let _userCoords = null;

    // Icono personalizado origen (amarillo)
    const iconOrigen = L.divIcon({
        className: '',
        html: `<div style="width:34px;height:34px;border-radius:50% 50% 50% 0;background:#dc2626;transform:rotate(-45deg);border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.3)"></div>`,
        iconSize: [34, 34], iconAnchor: [17, 34], popupAnchor: [0, -38]
    });

    // Icono destino (blanco)
    const iconDestino = L.divIcon({
        className: '',
        html: `<div style="width:34px;height:34px;border-radius:50% 50% 50% 0;background:#1f2937;transform:rotate(-45deg);border:3px solid #dc2626;box-shadow:0 2px 8px rgba(0,0,0,.3)"></div>`,
        iconSize: [34, 34], iconAnchor: [17, 34], popupAnchor: [0, -38]
    });

    // Icono transporte moviéndose
    const iconCar = L.divIcon({
        className: '',
        html: `<div style="width:28px;height:28px;border-radius:50%;background:#1f2937;display:flex;align-items:center;justify-content:center;border:2px solid #dc2626;box-shadow:0 2px 5px rgba(0,0,0,.4);color:#dc2626;font-size:12px;"><i class="fas fa-car-side"></i></div>`,
        iconSize: [28, 28], iconAnchor: [14, 14]
    });

    // Icono del usuario actual (pasajero)
    const iconUser = L.divIcon({
        className: '',
        html: `<div style="width:28px;height:28px;border-radius:50%;background:#3b82f6;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,.4);color:#fff;font-size:12px;"><i class="fas fa-street-view"></i></div>`,
        iconSize: [28, 28], iconAnchor: [14, 14], popupAnchor: [0, -14]
    });

    function init(containerId, data) {
        if (_map) { _map.remove(); _map = null; }

        _map = L.map(containerId, {
            center: data.centro || data.origen.coords,
            zoom: 14, zoomControl: true,
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap', maxZoom: 19
        }).addTo(_map);

        const markerOrigen = L.marker(data.origen.coords, { icon: iconOrigen }).addTo(_map)
            .bindPopup(`<b>🚀 Origen</b><br>${data.origen.zona}`, { maxWidth: 180 });

        const markerDestino = L.marker(data.destino.coords, { icon: iconDestino }).addTo(_map)
            .bindPopup(`<b>🏁 Destino</b><br>${data.destino.zona}`, { maxWidth: 180 });

        _drawRoute(data.origen.coords, data.destino.coords);

        const bounds = L.latLngBounds([data.origen.coords, data.destino.coords]);
        if (_userCoords) { bounds.extend(_userCoords); }
        _map.fitBounds(bounds.pad(0.15));

        setTimeout(() => markerOrigen.openPopup(), 600);

        if (_userCoords) {
            if (_userMarker) _map.removeLayer(_userMarker);
            _userMarker = L.marker(_userCoords, { icon: iconUser })
                .addTo(_map)
                .bindPopup(`<b>📍 Tú estás aquí</b> (Posición Real)`, { maxWidth: 180 });
        }
        return _map;
    }

    function _drawRoute(origenCoords, destinoCoords) {
        if (_simulationInterval) { clearInterval(_simulationInterval); }
        if (_carMarker) { _map.removeLayer(_carMarker); _carMarker = null; }

        const url = `https://router.project-osrm.org/route/v1/driving/` +
            `${origenCoords[1]},${origenCoords[0]};${destinoCoords[1]},${destinoCoords[0]}?overview=full&geometries=geojson`;

        fetch(url).then(r => r.json()).then(osrm => {
            if (osrm.code !== 'Ok' || !osrm.routes[0]) {
                _drawFallbackLine(origenCoords, destinoCoords);
                return;
            }
            const routeCoords = osrm.routes[0].geometry.coordinates; 
            const latLngs = routeCoords.map(coord => [coord[1], coord[0]]);
            if (_routeLayer) _map.removeLayer(_routeLayer);
            _animateTransport(latLngs);
        }).catch(() => _drawFallbackLine(origenCoords, destinoCoords));
    }

    function _animateTransport(latLngs) {
        if (latLngs.length === 0) return;
        let currentIndex = 0;
        
        _routeLayer = L.polyline(latLngs, {
            color: '#dc2626', weight: 5, opacity: 0.85
        }).addTo(_map);

        _carMarker = L.marker(latLngs[0], { icon: iconCar }).addTo(_map);

        _simulationInterval = setInterval(() => {
            currentIndex++;
            if (currentIndex >= latLngs.length) {
                clearInterval(_simulationInterval);
                return;
            }

            const currentPos = latLngs[currentIndex];
            _carMarker.setLatLng(currentPos);

            if (_userCoords) {
                const distMetros = L.latLng(currentPos).distanceTo(L.latLng(_userCoords));
                const distNode = document.getElementById('distancia-al-usuario');
                if (distNode) {
                    distNode.textContent = distMetros > 1000 
                        ? (distMetros / 1000).toFixed(1) + ' km'
                        : Math.round(distMetros) + ' m';
                }
            }

            _routeLayer.setLatLngs(latLngs.slice(currentIndex));
        }, 120);
    }

    function _drawFallbackLine(origenCoords, destinoCoords) {
        if (_routeLayer) _map.removeLayer(_routeLayer);
        const points = [];
        const steps = 30;
        for (let i = 0; i <= steps; i++) {
            points.push([
                origenCoords[0] + (destinoCoords[0] - origenCoords[0]) * (i / steps),
                origenCoords[1] + (destinoCoords[1] - origenCoords[1]) * (i / steps)
            ]);
        }
        _animateTransport(points);
    }

    function cargarViaje(viajeId, containerId, statsContainerId) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '<div class="spinner"></div>';
        
        // 1. Pedir ubicación real primero
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition((pos) => {
                _userCoords = [pos.coords.latitude, pos.coords.longitude];
                _fetchAndDraw(viajeId, containerId, statsContainerId, true);
            }, (error) => {
                console.log("No se pudo obtener ubicación:", error.message);
                _userCoords = null;
                _fetchAndDraw(viajeId, containerId, statsContainerId, false);
            }, { timeout: 8000 });
        } else {
            _userCoords = null;
            _fetchAndDraw(viajeId, containerId, statsContainerId, false);
        }
    }

    function _fetchAndDraw(viajeId, containerId, statsContainerId, useUserLoc) {
        fetch(`/api/v1/viajes/${viajeId}/mapa`)
            .then(r => r.json())
            .then(data => {
                const el = document.getElementById(containerId);
                el.innerHTML = ''; el.id = containerId; el.style.height = '380px';

                if (useUserLoc && _userCoords) {
                    // TRUCO AVANZADO DESPLIEGUE: Trasladar las coordenadas ficticias (Ecuador) a las calles
                    // Reales de donde está físicamente parado el usuario ahora mismo.
                    const rLat = _userCoords[0];
                    const rLng = _userCoords[1];

                    // Calcular offset global entre la coordenada vieja base (Ecuador) y el usuario actual
                    // El origen arrancará unos ~800 metros noroeste de donde está el usuario 
                    // para que el mapa dibuje calles reales de la ciudad del cliente.
                    const dLat = rLat - data.origen.coords[0] - 0.007;
                    const dLng = rLng - data.origen.coords[1] - 0.007;

                    data.origen.coords[0] += dLat;
                    data.origen.coords[1] += dLng;
                    
                    data.destino.coords[0] += dLat;
                    data.destino.coords[1] += dLng;

                    data.centro[0] += dLat;
                    data.centro[1] += dLng;
                }

                init(containerId, data);
                _updateStats(data, statsContainerId);
            })
            .catch(err => {
                const el = document.getElementById(containerId);
                if (el) el.innerHTML = `<div style="text-align:center;padding:40px;color:#6b7280"><i class="fas fa-map-marked-alt" style="font-size:3rem;color:#dc2626"></i><p style="margin-top:12px">Mapa no disponible</p></div>`;
            });
    }

    function _updateStats(data, containerId) {
        const el = document.getElementById(containerId);
        if (!el) return;

        el.innerHTML = `
        <div class="mapa-data-grid" style="grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));">
            <div class="mapa-stat" style="grid-column: 1 / -1; background: rgba(201,162,39,.1); padding: 10px; border-radius: 8px;">
                <div class="mapa-stat-num" id="distancia-al-usuario" style="color:#dc2626; font-size: 1.6rem;">--</div>
                <div class="mapa-stat-label" style="color:#dc2626; font-weight:bold; letter-spacing: 0.5px;">
                    <i class="fas fa-street-view"></i> DISTANCIA AL TRANSPORTE
                </div>
            </div>
            <div class="mapa-stat">
                <div class="mapa-stat-num">${data.distancia_km} <small>km</small></div>
                <div class="mapa-stat-label">Ruta Total</div>
            </div>
            <div class="mapa-stat">
                <div class="mapa-stat-num">${data.tiempo_estimado_min} <small>min</small></div>
                <div class="mapa-stat-label">Tiempo Est.</div>
            </div>
            <div class="mapa-stat">
                <div class="mapa-stat-num">${data.cupos_disponibles}/${data.cupos_totales}</div>
                <div class="mapa-stat-label">Cupos Libres</div>
            </div>
        </div>`;
    }

    return { init, cargarViaje };
})();
