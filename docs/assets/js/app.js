(function () {
    var MAP_POLL_MS = 80;
    var MAX_ATTEMPTS = 60;

    function stripHtmlAndTrim(str) {
        return str.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function getPopupText(marker) {
        var popup = marker.getPopup();
        if (!popup) return '';
        var content = popup.getContent();
        if (!content) return '';
        if (typeof content === 'string') return stripHtmlAndTrim(content);
        if (content.outerHTML) return stripHtmlAndTrim(content.outerHTML);
        if (content.innerHTML) return stripHtmlAndTrim(content.innerHTML);
        if (content.textContent) return content.textContent.trim();
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

        // ===== RAIO DE INFLUÊNCIA =====
        var raioAtivo = false;
        var raioCircle = null;
        var btnRaio = document.getElementById('btn-raio');
        var raioSelect = document.getElementById('raio-select');
        var raioInfo = document.getElementById('raio-info');

        function getTooltipText(marker) {
            var tooltip = marker.getTooltip();
            if (!tooltip) return '';
            var content = tooltip.getContent();
            if (!content) return '';
            if (typeof content === 'string') return stripHtmlAndTrim(content);
            if (content && content.textContent) return content.textContent.trim();
            return '';
        }

        function limparRaio() {
            if (raioCircle) {
                mapInstance.removeLayer(raioCircle);
                raioCircle = null;
            }
            raioInfo.style.display = 'none';
            allMarkers.forEach(function (m) { m.setOpacity(1.0); });
        }

        function toggleRaio() {
            raioAtivo = !raioAtivo;
            btnRaio.textContent = raioAtivo ? 'DESATIVAR' : 'ATIVAR';
            btnRaio.style.borderColor = raioAtivo ? 'var(--cor-primaria,#00ffcc)' : '#666';
            if (!raioAtivo) limparRaio();
        }

        allMarkers.forEach(function (marker) {
            marker.on('click', function () {
                if (!raioAtivo) return;
                limparRaio();

                var center = marker.getLatLng();
                var radius = parseInt(raioSelect.value, 10);

                raioCircle = L.circle(center, {
                    radius: radius,
                    color: 'var(--cor-primaria,#00ffcc)',
                    fillColor: 'var(--cor-primaria,#00ffcc)',
                    fillOpacity: 0.12,
                    weight: 2,
                }).addTo(mapInstance);

                var dentro = [], seen = {};
                allMarkers.forEach(function (m) {
                    var d = m.getLatLng().distanceTo(center);
                    if (d <= radius) {
                        var tt = getTooltipText(m);
                        if (!seen[tt]) {
                            seen[tt] = true;
                            dentro.push(m);
                        }
                        m.setOpacity(1.0);
                    } else {
                        m.setOpacity(0.25);
                    }
                });

                var totalVotos = 0;
                dentro.forEach(function (m) {
                    var tt = getTooltipText(m);
                    if (window.markerData && window.markerData[tt]) {
                        totalVotos += window.markerData[tt].total;
                    }
                });

                raioInfo.style.display = 'block';
                raioInfo.innerHTML =
                    '<strong style="color:var(--cor-primaria,#00ffcc);">📊 RAIO DE INFLUÊNCIA</strong><br>' +
                    'Raio: <strong>' + radius + ' m</strong><br>' +
                    'Locais de votação: <strong>' + dentro.length + '</strong><br>' +
                    'Total de eleitores: <strong style="color:var(--cor-primaria,#00ffcc);">' + totalVotos.toLocaleString() + '</strong>';
            });
        });

        if (btnRaio) {
            btnRaio.addEventListener('click', toggleRaio);
        }
        if (raioSelect) {
            raioSelect.addEventListener('change', function () {
                if (raioAtivo && raioCircle) {
                    raioCircle.setRadius(parseInt(raioSelect.value, 10));
                }
            });
        }

        // ===== EXPORTAR RELATÓRIO =====
        var btnExportar = document.getElementById('btn-exportar');
        function exportarRelatorio() {
            var nomeCandidato = getComputedStyle(document.documentElement).getPropertyValue('--nome-candidato').replace(/"/g,'').trim() || 'NÃO CONFIGURADO';
            var totalGeral = 0;
            var stdCount = 0, volCount = 0;
            allMarkers.forEach(function (m) {
                var tt = getTooltipText(m);
                if (window.markerData && window.markerData[tt]) {
                    totalGeral += window.markerData[tt].total;
                    if (window.markerData[tt].is_volatil) volCount++;
                    else stdCount++;
                }
            });

            var raioContent = '';
            if (raioCircle && raioInfo.style.display === 'block') {
                raioContent = raioInfo.innerHTML.replace(/<strong[^>]*>/g,'**').replace(/<\/strong>/g,'**').replace(/<br>/g,'\n');
            }

            var printWin = window.open('','_blank','width=800,height=600');
            printWin.document.write('<!DOCTYPE html><html><head><title>Relatório Eleitoral</title>');
            printWin.document.write('<style>');
            printWin.document.write('body{font-family:Arial,sans-serif;padding:40px;color:#222;}');
            printWin.document.write('h1{color:#00e676;border-bottom:2px solid #00e676;padding-bottom:10px;}');
            printWin.document.write('h2{color:#333;margin-top:30px;}');
            printWin.document.write('table{width:100%;border-collapse:collapse;margin:15px 0;}');
            printWin.document.write('th,td{border:1px solid #ccc;padding:8px 12px;text-align:left;}');
            printWin.document.write('th{background:#00e676;color:#fff;}');
            printWin.document.write('.destaque{font-weight:700;color:#00e676;}');
            printWin.document.write('.info{background:#f9f9f9;padding:15px;border-radius:6px;margin:15px 0;}');
            printWin.document.write('.info pre{white-space:pre-wrap;font-family:inherit;margin:0;}');
            printWin.document.write('@media print{body{padding:20px;}button{display:none;}}');
            printWin.document.write('</style></head><body>');
            printWin.document.write('<h1>🗳️ RELATÓRIO ELEITORAL — ' + nomeCandidato + '</h1>');
            printWin.document.write('<p>Gerado em: <strong>' + new Date().toLocaleString('pt-BR') + '</strong></p>');

            printWin.document.write('<h2>📊 RESUMO GERAL</h2>');
            printWin.document.write('<table><tr><th>Indicador</th><th>Valor</th></tr>');
            printWin.document.write('<tr><td>Total de locais de votação</td><td class="destaque">' + allMarkers.length + '</td></tr>');
            printWin.document.write('<tr><td>Locais estáveis</td><td>' + stdCount + '</td></tr>');
            printWin.document.write('<tr><td>Zonas voláteis</td><td>' + volCount + '</td></tr>');
            printWin.document.write('<tr><td>Total de eleitores</td><td class="destaque">' + totalGeral.toLocaleString() + '</td></tr>');
            printWin.document.write('</table>');

            if (raioContent) {
                printWin.document.write('<h2>📐 RAIO DE INFLUÊNCIA</h2>');
                printWin.document.write('<div class="info"><pre>' + raioContent + '</pre></div>');
            }

            printWin.document.write('<h2>📍 TOP 10 LOCAIS (MAIORES)</h2>');
            printWin.document.write('<table><tr><th>#</th><th>Local</th><th>Município</th><th>Eleitores</th></tr>');
            var sorted = allMarkers.slice().sort(function (a,b) {
                var ta = getTooltipText(a), tb = getTooltipText(b);
                var da = window.markerData && window.markerData[ta] ? window.markerData[ta].total : 0;
                var db = window.markerData && window.markerData[tb] ? window.markerData[tb].total : 0;
                return db - da;
            });
            sorted.slice(0,10).forEach(function (m,i) {
                var tt = getTooltipText(m);
                var parts = tt.split(' (');
                var local = parts[0] || tt;
                var muni = parts[1] ? parts[1].replace(')','') : '';
                var total = window.markerData && window.markerData[tt] ? window.markerData[tt].total : 0;
                printWin.document.write('<tr><td>' + (i+1) + '</td><td>' + local + '</td><td>' + muni + '</td><td class="destaque">' + total.toLocaleString() + '</td></tr>');
            });
            printWin.document.write('</table>');

            printWin.document.write('<p style="margin-top:40px;font-size:11px;color:#999;">MapsTSE — Sistema de Inteligência Eleitoral</p>');
            printWin.document.write('</body></html>');
            printWin.document.close();
            printWin.print();
        }
        if (btnExportar) {
            btnExportar.addEventListener('click', exportarRelatorio);
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
