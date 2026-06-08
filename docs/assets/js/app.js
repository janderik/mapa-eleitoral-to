(function () {
    var MAP_POLL_MS = 80;
    var MAX_ATTEMPTS = 60;

    function getPopupText(marker) {
        var popup = marker.getPopup();
        if (!popup) return '';
        var content = popup.getContent();
        if (!content) return '';
        if (typeof content === 'string') return content;
        if (content.outerHTML) return content.outerHTML;
        if (content.innerHTML) return content.innerHTML;
        if (content.textContent) return content.textContent;
        return content.toString ? content.toString() : '';
    }

    function collectAllMarkers(mapInstance) {
        var markers = [];
        mapInstance.eachLayer(function (layer) {
            if (layer instanceof L.Marker) {
                markers.push(layer);
            } else if (layer.eachLayer) {
                layer.eachLayer(function (child) {
                    if (child instanceof L.Marker) {
                        markers.push(child);
                    }
                });
            }
        });
        return markers;
    }

    function onMapReady(mapInstance) {
        // ===== SIDEBAR TOGGLE =====
        var sb = document.getElementById('control-sidebar');
        var btn = document.getElementById('sidebar-toggle');
        if (btn) {
            btn.addEventListener('click', function () {
                sb.classList.toggle('open');
                btn.textContent = sb.classList.contains('open') ? '\u2715 FECHAR' : '\u2699\ufe0f FILTROS';
            });
        }
        document.addEventListener('click', function (e) {
            if (sb && sb.classList.contains('open') && !sb.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
                sb.classList.remove('open');
                if (btn) btn.textContent = '\u2699\ufe0f FILTROS';
            }
        });

        // ===== CITY SEARCH (flyTo) =====
        var searchCity = document.getElementById('search-city');
        if (searchCity) {
            searchCity.addEventListener('change', function (e) {
                var cityName = e.target.value.toUpperCase().trim();
                if (window.cityCoords && window.cityCoords[cityName]) {
                    mapInstance.flyTo(window.cityCoords[cityName], 13, { animate: true, duration: 1.5 });
                }
            });
        }

        // ===== CANDIDATE FILTER =====
        var inputCandidato = document.getElementById('input-candidato');
        var btnLimpar = document.getElementById('btn-limpar-candidato');
        var allMarkers = collectAllMarkers(mapInstance);

        function filtrarCandidato() {
            var termo = inputCandidato.value.toUpperCase().trim();
            if (termo === '') return;

            var anyMatch = false;
            allMarkers.forEach(function (marker) {
                var textoPopup = getPopupText(marker).toUpperCase();
                if (textoPopup.includes(termo)) {
                    anyMatch = true;
                    if (!mapInstance.hasLayer(marker)) {
                        mapInstance.addLayer(marker);
                    }
                    marker.setOpacity(1.0);
                } else {
                    if (mapInstance.hasLayer(marker)) {
                        mapInstance.removeLayer(marker);
                    }
                }
            });
            if (!anyMatch) {
                limparFiltro();
                alert('Nenhum local encontrado com vota\u00e7\u00f5es para este candidato.');
            }
        }

        function limparFiltro() {
            inputCandidato.value = '';
            allMarkers.forEach(function (marker) {
                if (!mapInstance.hasLayer(marker)) {
                    mapInstance.addLayer(marker);
                }
                marker.setOpacity(1.0);
            });
        }

        if (inputCandidato) {
            inputCandidato.addEventListener('change', filtrarCandidato);
            inputCandidato.addEventListener('keypress', function (e) {
                if (e.key === 'Enter' && e.target.value.trim()) {
                    filtrarCandidato();
                }
            });
        }
        if (btnLimpar) {
            btnLimpar.addEventListener('click', limparFiltro);
        }

        // ===== VOLATILITY TOGGLE =====
        var vulnFilter = document.getElementById('vulnerability-filter');
        if (vulnFilter) {
            vulnFilter.addEventListener('change', function (e) {
                var fg = window[window.fgVolatilName];
                if (!fg) return;
                if (e.target.checked) {
                    mapInstance.addLayer(fg);
                } else {
                    mapInstance.removeLayer(fg);
                }
            });
        }

        // ===== TOP 10 TOGGLE =====
        window.toggleTop10 = function () {
            var body = document.getElementById('top10-body');
            var btnToggle = document.getElementById('top10-toggle');
            if (!body || !btnToggle) return;
            if (body.style.display === 'none') {
                body.style.display = '';
                btnToggle.textContent = '\u2212';
            } else {
                body.style.display = 'none';
                btnToggle.textContent = '+';
            }
        };
        if (window.innerWidth <= 768) {
            var body = document.getElementById('top10-body');
            var btnToggle = document.getElementById('top10-toggle');
            if (body) body.style.display = 'none';
            if (btnToggle) btnToggle.textContent = '+';
        }
    }

    // Poll until the Folium map is available
    var attempts = 0;
    var pollTimer = setInterval(function () {
        var mapInstance = null;
        for (var key in window) {
            if (key.startsWith('map_') && window[key] instanceof L.Map) {
                mapInstance = window[key];
                break;
            }
        }
        if (mapInstance) {
            clearInterval(pollTimer);
            onMapReady(mapInstance);
            return;
        }
        attempts++;
        if (attempts >= MAX_ATTEMPTS) {
            clearInterval(pollTimer);
        }
    }, MAP_POLL_MS);
})();
