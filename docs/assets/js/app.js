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

        // ===== HELPER FUNCTIONS =====
        function parseTooltip(tt) {
            var idx = tt.indexOf(' (');
            if (idx === -1) return { local: tt, municipio: '' };
            return { local: tt.substring(0, idx), municipio: tt.substring(idx + 2, tt.length - 1) };
        }

        function getVisibleMarkers() {
            var seen = {}, result = [], bounds = mapInstance.getBounds();
            allMarkers.forEach(function (m) {
                if (!mapInstance.hasLayer(m)) return;
                if (!bounds.contains(m.getLatLng())) return;
                var tt = getTooltipText(m);
                if (!seen[tt] && window.markerData && window.markerData[tt]) {
                    seen[tt] = true;
                    result.push(m);
                }
            });
            return result;
        }

        function atualizarMetricas() {
            var painel = document.getElementById('painel-metricas');
            if (!painel) return;
            var visiveis = getVisibleMarkers();
            if (visiveis.length === 0) {
                painel.innerHTML = '<div style="color:#bbb;text-align:center;padding:10px;">Nenhum local visível</div>';
                return;
            }

            var totalEleitores = 0;
            var volCount = 0;
            var maiorLocal = null, maiorTotal = 0;
            var menorLocal = null, menorTotal = Infinity;
            var generos = {};

            visiveis.forEach(function (m) {
                var tt = getTooltipText(m);
                var d = window.markerData[tt];
                totalEleitores += d.total;
                if (d.is_volatil) volCount++;
                if (d.total > maiorTotal) { maiorTotal = d.total; maiorLocal = tt; }
                if (d.total < menorTotal) { menorTotal = d.total; menorLocal = tt; }
                if (d.generos) {
                    for (var g in d.generos) {
                        if (d.generos.hasOwnProperty(g)) {
                            generos[g] = (generos[g] || 0) + d.generos[g];
                        }
                    }
                }
            });

            var totalLocais = visiveis.length;
            var media = Math.round(totalEleitores / totalLocais);
            var stdCount = totalLocais - volCount;
            var pctVol = totalLocais > 0 ? ((volCount / totalLocais) * 100).toFixed(1) : '0.0';

            var pMaior = maiorLocal ? parseTooltip(maiorLocal) : { local: '-', municipio: '' };
            var pMenor = menorLocal ? parseTooltip(menorLocal) : { local: '-', municipio: '' };

            var munisVisiveis = {}, munisList = [];
            visiveis.forEach(function (m) {
                var tt = getTooltipText(m);
                var p = parseTooltip(tt);
                if (p.municipio && !munisVisiveis[p.municipio]) {
                    munisVisiveis[p.municipio] = true;
                    munisList.push(p.municipio);
                }
            });
            var labelRegiao = '';
            if (munisList.length === 0) labelRegiao = '';
            else if (munisList.length === 1) labelRegiao = munisList[0];
            else if (munisList.length <= 3) labelRegiao = munisList.join(', ');
            else labelRegiao = munisList.length + ' municípios';

            html = '<div style="font-weight:700;color:var(--cor-primaria,#00ffcc);margin-bottom:8px;">📊 MÉTRICAS</div>';
            if (labelRegiao) {
                html += '<div style="font-size:11px;color:#999;margin-bottom:6px;border-bottom:1px solid #2a2a2a;padding-bottom:6px;">📍 ' + labelRegiao + '</div>';
            }
            html += '<div style="margin-bottom:8px;">';
            html += '<div>👥 Total: <strong style="color:#fff;">' + totalEleitores.toLocaleString() + '</strong> eleitores</div>';
            html += '<div>📍 Locais: <strong style="color:#fff;">' + totalLocais + '</strong> visíveis</div>';
            html += '<div>📊 Média: <strong style="color:#fff;">' + media.toLocaleString() + '</strong> por local</div>';
            html += '</div>';

            var genKeys = Object.keys(generos);
            if (genKeys.length > 0) {
                html += '<div style="font-size:11px;color:#ccc;margin-bottom:4px;">🚻 GÊNERO</div>';
                var ordem = ['FEMININO', 'MASCULINO', 'NÃO INFORMADO'];
                ordem.forEach(function (g) {
                    if (generos[g] === undefined) return;
                    var pct = ((generos[g] / totalEleitores) * 100).toFixed(1);
                    var cor = g === 'FEMININO' ? '#e84393' : (g === 'MASCULINO' ? '#0984e3' : '#95a5a6');
                    html += '<div style="margin-bottom:3px;">';
                    html += '<div style="display:flex;justify-content:space-between;font-size:11px;">';
                    html += '<span>' + g.charAt(0) + g.substring(1).toLowerCase() + '</span>';
                    html += '<span style="color:' + cor + ';font-weight:600;">' + pct + '%</span>';
                    html += '</div>';
                    html += '<div style="background:#333;border-radius:3px;height:6px;margin-top:1px;">';
                    html += '<div style="width:' + pct + '%;background:' + cor + ';height:6px;border-radius:3px;"></div>';
                    html += '</div></div>';
                });
            }

            html += '<div style="margin-top:6px;font-size:11px;color:#ccc;">⚡ VOLATILIDADE</div>';
            html += '<div style="display:flex;justify-content:space-between;font-size:11px;margin-top:2px;">';
            html += '<span>Estáveis: <strong style="color:#2ecc71;">' + stdCount + '</strong> (' + (100 - parseFloat(pctVol)).toFixed(1) + '%)</span>';
            html += '<span>Voláteis: <strong style="color:#e74c3c;">' + volCount + '</strong> (' + pctVol + '%)</span>';
            html += '</div>';

            html += '<div style="margin-top:8px;padding-top:6px;border-top:1px solid #333;font-size:11px;">';
            html += '<div style="color:#ccc;margin-bottom:3px;">📈 RANKING</div>';
            html += '<div>🟢 Maior: <strong style="color:#fff;">' + pMaior.local + '</strong> (' + pMaior.municipio + ') — <strong style="color:var(--cor-primaria,#00ffcc);">' + maiorTotal.toLocaleString() + '</strong></div>';
            html += '<div>🔴 Menor: <strong style="color:#fff;">' + pMenor.local + '</strong> (' + pMenor.municipio + ') — <strong style="color:var(--cor-primaria,#00ffcc);">' + menorTotal.toLocaleString() + '</strong></div>';
            html += '</div>';

            painel.innerHTML = html;
        }

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
                return;
            }
            atualizarMetricas();
        }

        function limparFiltro() {
            inputCandidato.value = '';
            allMarkers.forEach(function (marker) {
                if (!mapInstance.hasLayer(marker)) {
                    mapInstance.addLayer(marker);
                }
                marker.setOpacity(1.0);
            });
            atualizarMetricas();
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
                atualizarMetricas();
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

        function buildUniqueMarkers() {
            var seen = {}, result = [];
            allMarkers.forEach(function (m) {
                var tt = getTooltipText(m);
                if (!seen[tt] && window.markerData && window.markerData[tt]) {
                    seen[tt] = true;
                    result.push(m);
                }
            });
            return result;
        }

        function parseTooltip(tt) {
            var idx = tt.indexOf(' (');
            if (idx === -1) return { local: tt, municipio: '' };
            return { local: tt.substring(0, idx), municipio: tt.substring(idx + 2, tt.length - 1) };
        }

        function exportarRelatorio() {
            var corPrimaria = getComputedStyle(document.documentElement).getPropertyValue('--cor-primaria').trim() || '#00ffcc';
            var corSecundaria = getComputedStyle(document.documentElement).getPropertyValue('--cor-secundaria').trim() || '#00e676';
            var nomeCandidato = getComputedStyle(document.documentElement).getPropertyValue('--nome-candidato').replace(/"/g,'').trim() || 'NÃO CONFIGURADO';

            var unicos = buildUniqueMarkers();
            var totalGeral = 0, volCount = 0, municipios = {};
            unicos.forEach(function (m) {
                var tt = getTooltipText(m);
                var d = window.markerData[tt];
                totalGeral += d.total;
                if (d.is_volatil) volCount++;
                var parsed = parseTooltip(tt);
                municipios[parsed.municipio] = true;
            });
            var stdCount = unicos.length - volCount;
            var qtdMunicipios = Object.keys(municipios).length;

            var top10Html = '';
            var sorted = unicos.slice().sort(function (a, b) {
                var da = window.markerData[getTooltipText(a)].total;
                var db = window.markerData[getTooltipText(b)].total;
                return db - da;
            });
            sorted.slice(0, 10).forEach(function (m, i) {
                var tt = getTooltipText(m);
                var p = parseTooltip(tt);
                var total = window.markerData[tt].total;
                top10Html += '<tr><td>' + (i + 1) + '</td><td>' + p.local + '</td><td>' + p.municipio + '</td><td class="destaque">' + total.toLocaleString() + '</td></tr>';
            });

            var raioHtml = '';
            if (raioCircle && raioInfo.style.display === 'block') {
                var centro = raioCircle.getLatLng();
                var raioM = parseInt(raioSelect.value, 10);
                var locaisDentro = [], seenR = {};
                allMarkers.forEach(function (m) {
                    var d = m.getLatLng().distanceTo(centro);
                    if (d <= raioM) {
                        var tt = getTooltipText(m);
                        if (!seenR[tt] && window.markerData && window.markerData[tt]) {
                            seenR[tt] = true;
                            locaisDentro.push(m);
                        }
                    }
                });
                var votosRaio = 0;
                locaisDentro.forEach(function (m) {
                    votosRaio += window.markerData[getTooltipText(m)].total;
                });
                raioHtml =
                    '<h2 style="color:' + corPrimaria + ';margin-top:30px;">📐 RAIO DE INFLUÊNCIA</h2>' +
                    '<table><tr><th>Indicador</th><th>Valor</th></tr>' +
                    '<tr><td>Raio configurado</td><td class="destaque">' + raioM + ' m</td></tr>' +
                    '<tr><td>Locais de votação</td><td class="destaque">' + locaisDentro.length + '</td></tr>' +
                    '<tr><td>Total de eleitores</td><td class="destaque">' + votosRaio.toLocaleString() + '</td></tr></table>';
            }

            var css = '' +
                'body{font-family:Segoe UI,Arial,sans-serif;padding:50px 60px;color:#222;max-width:900px;margin:0 auto;}' +
                '.header{text-align:center;padding-bottom:20px;border-bottom:3px solid ' + corPrimaria + ';margin-bottom:30px;}' +
                '.header h1{color:' + corPrimaria + ';margin:0 0 5px 0;font-size:26px;letter-spacing:1px;}' +
                '.header p{margin:0;color:#888;font-size:13px;}' +
                'h2{color:' + corSecundaria + ';font-size:18px;margin-top:35px;margin-bottom:10px;}' +
                'table{width:100%;border-collapse:collapse;margin:10px 0 20px 0;font-size:14px;}' +
                'th{background:' + corPrimaria + ';color:#000;padding:10px 14px;text-align:left;font-weight:700;}' +
                'td{border:1px solid #ddd;padding:9px 14px;}' +
                'tr:nth-child(even){background:#f8f8f8;}' +
                '.destaque{font-weight:700;color:' + corPrimaria + ';}' +
                '.footer{text-align:center;margin-top:50px;padding-top:15px;border-top:1px solid #ddd;font-size:11px;color:#aaa;}' +
                '@media print{body{padding:30px 40px;}}';

            var printWin = window.open('', '_blank', 'width=900,height=700');
            var doc = printWin.document;
            doc.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Relatório Eleitoral — ' + nomeCandidato + '</title><style>' + css + '</style></head><body>');
            doc.write('<div class="header"><h1>🗳️ RELATÓRIO ELEITORAL</h1><p>' + nomeCandidato + ' — Gerado em ' + new Date().toLocaleString('pt-BR') + '</p></div>');
            doc.write('<h2>📊 RESUMO GERAL</h2>');
            doc.write('<table><tr><th style="width:60%;">Indicador</th><th>Valor</th></tr>');
            doc.write('<tr><td>Total de locais de votação</td><td class="destaque">' + unicos.length + '</td></tr>');
            doc.write('<tr><td>Locais estáveis</td><td>' + stdCount + '</td></tr>');
            doc.write('<tr><td>Zonas voláteis</td><td><span style="color:#e74c3c;font-weight:700;">' + volCount + '</span></td></tr>');
            doc.write('<tr><td>Municípios abrangidos</td><td>' + qtdMunicipios + '</td></tr>');
            doc.write('<tr><td>Total de eleitores</td><td class="destaque">' + totalGeral.toLocaleString() + '</td></tr>');
            doc.write('</table>');
            if (raioHtml) doc.write(raioHtml);
            doc.write('<h2>📍 TOP 10 LOCAIS (MAIORES)</h2>');
            doc.write('<table><tr><th style="width:40px;">#</th><th>Local</th><th>Município</th><th style="width:100px;">Eleitores</th></tr>');
            doc.write(top10Html);
            doc.write('</table>');
            doc.write('<div class="footer">MapsTSE — Sistema de Inteligência Eleitoral</div>');
            doc.write('</body></html>');
            doc.close();
            printWin.print();
        }
        if (btnExportar) {
            btnExportar.addEventListener('click', exportarRelatorio);
        }

        // ===== COMPARATIVO A vs B =====
        var cmpGroup = null, cmpAtivo = false;
        var cmpSelectA = document.getElementById('cmp-cand-a');
        var cmpSelectB = document.getElementById('cmp-cand-b');
        var btnComparar = document.getElementById('btn-comparar');
        var btnLimparCmp = document.getElementById('btn-limpar-cmp');
        var cmpResultado = document.getElementById('cmp-resultado');

        function buildUniqueMarkers() {
            var seen = {}, result = [];
            allMarkers.forEach(function (m) {
                var tt = getTooltipText(m);
                if (!seen[tt] && window.markerData && window.markerData[tt]) {
                    seen[tt] = true;
                    result.push(m);
                }
            });
            return result;
        }

        function corPorCandidato() {
            var candA = cmpSelectA.value.trim();
            var candB = cmpSelectB.value.trim();
            if (!candA || !candB || candA === candB) return null;
            var unicos = buildUniqueMarkers();
            var ganhaA = 0, ganhaB = 0, empate = 0, semDados = 0;
            var totalVotosA = 0, totalVotosB = 0;
            var resultados = [];

            unicos.forEach(function (m) {
                var tt = getTooltipText(m);
                var votos = window.votosPorLocal && window.votosPorLocal[tt];
                var vA = votos && votos[candA] !== undefined ? votos[candA] : undefined;
                var vB = votos && votos[candB] !== undefined ? votos[candB] : undefined;
                if (vA === undefined && vB === undefined) { semDados++; return; }
                var latlng = m.getLatLng();
                var cor, vencedor;
                if (vA !== undefined && vB !== undefined) {
                    if (vA > vB) { cor = '#2ecc71'; vencedor = candA; ganhaA++; totalVotosA += vA; }
                    else if (vB > vA) { cor = '#3498db'; vencedor = candB; ganhaB++; totalVotosB += vB; }
                    else { cor = '#95a5a6'; vencedor = 'Empate'; empate++; }
                } else if (vA !== undefined) {
                    cor = '#2ecc71'; vencedor = candA; ganhaA++; totalVotosA += vA;
                } else {
                    cor = '#3498db'; vencedor = candB; ganhaB++; totalVotosB += vB;
                }
                resultados.push({ latlng: latlng, cor: cor, tt: tt, vencedor: vencedor });
            });
            return { resultados: resultados, candA: candA, candB: candB, ganhaA: ganhaA, ganhaB: ganhaB, empate: empate, semDados: semDados, totalVotosA: totalVotosA, totalVotosB: totalVotosB };
        }

        function getRawPopupContent(marker) {
            var popup = marker.getPopup();
            if (!popup) return '';
            var content = popup.getContent();
            if (!content) return '';
            if (typeof content === 'string') return content;
            if (content.outerHTML) return content.outerHTML;
            return '';
        }

        function iniciarComparativo() {
            if (cmpGroup) { mapInstance.removeLayer(cmpGroup); cmpGroup = null; }
            var data = corPorCandidato();
            if (!data) { alert('Selecione dois candidatos diferentes para comparar.'); return; }
            cmpAtivo = true;
            cmpGroup = L.featureGroup();

            var ttToMarker = {};
            allMarkers.forEach(function (m) {
                var tt = getTooltipText(m);
                if (!ttToMarker[tt]) ttToMarker[tt] = m;
            });

            data.resultados.forEach(function (r) {
                var original = ttToMarker[r.tt];
                var cm = L.circleMarker(r.latlng, {
                    radius: 9,
                    color: r.cor,
                    fillColor: r.cor,
                    fillOpacity: 0.85,
                    weight: 2,
                    opacity: 1,
                });
                if (original) {
                    var pc = getRawPopupContent(original);
                    if (pc) cm.bindPopup(pc, { maxWidth: 380 });
                    var tooltip = original.getTooltip();
                    if (tooltip) {
                        var tc = tooltip.getContent();
                        if (tc) cm.bindTooltip(tc);
                    }
                }
                cmpGroup.addLayer(cm);
            });
            mapInstance.addLayer(cmpGroup);
            allMarkers.forEach(function (m) { m.setOpacity(0.12); });
            atualizarMetricas();

            var totalGeral = data.ganhaA + data.ganhaB + data.empate;
            var pctA = totalGeral > 0 ? ((data.ganhaA / totalGeral) * 100).toFixed(1) : 0;
            var pctB = totalGeral > 0 ? ((data.ganhaB / totalGeral) * 100).toFixed(1) : 0;
            var largA = Math.max(parseFloat(pctA), 3);
            var largB = Math.max(parseFloat(pctB), 3);

            cmpResultado.style.display = 'block';
            cmpResultado.innerHTML =
                '<div style="font-weight:700;color:var(--cor-primaria,#00ffcc);margin-bottom:8px;">⚔️ COMPARATIVO</div>' +
                '<div style="margin-bottom:8px;"><span style="color:#2ecc71;font-weight:700;">' + data.candA + '</span> vence em <strong>' + data.ganhaA + '</strong> locais</div>' +
                '<div style="height:20px;background:#333;border-radius:4px;overflow:hidden;margin-bottom:6px;display:flex;position:relative;">' +
                '<div style="width:' + largA + '%;background:#2ecc71;height:20px;transition:width .3s;text-align:center;font-size:10px;line-height:20px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;">' + data.ganhaA + '</div>' +
                '<div style="flex:1;"></div>' +
                '</div>' +
                '<div style="margin-bottom:8px;"><span style="color:#3498db;font-weight:700;">' + data.candB + '</span> vence em <strong>' + data.ganhaB + '</strong> locais</div>' +
                '<div style="height:20px;background:#333;border-radius:4px;overflow:hidden;margin-bottom:6px;display:flex;position:relative;">' +
                '<div style="flex:1;"></div>' +
                '<div style="width:' + largB + '%;background:#3498db;height:20px;transition:width .3s;text-align:center;font-size:10px;line-height:20px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;">' + data.ganhaB + '</div>' +
                '</div>' +
                (data.empate > 0 ? '<div style="color:#95a5a6;">Empates: <strong>' + data.empate + '</strong></div>' : '') +
                (data.semDados > 0 ? '<div style="color:#666;font-size:11px;">Sem dados: ' + data.semDados + ' locais</div>' : '');
        }

        function limparComparativo() {
            if (cmpGroup) { mapInstance.removeLayer(cmpGroup); cmpGroup = null; }
            cmpAtivo = false;
            cmpResultado.style.display = 'none';
            allMarkers.forEach(function (m) { m.setOpacity(1.0); });
            atualizarMetricas();
        }

        if (btnComparar) {
            btnComparar.addEventListener('click', function () {
                if (cmpAtivo) limparComparativo();
                iniciarComparativo();
            });
        }
        if (btnLimparCmp) {
            btnLimparCmp.addEventListener('click', limparComparativo);
        }

        // ===== MODO APRESENTAÇÃO =====
        var modoApres = false;
        var btnApres = document.getElementById('btn-apresentacao');
        var btnSairApres = null;
        var sbToggle = document.getElementById('sidebar-toggle');

        function entrarApresentacao() {
            if (modoApres) return;
            modoApres = true;
            document.body.classList.add('modo-apresentacao');
            if (sb && sb.classList.contains('open')) {
                sb.classList.remove('open');
                if (sbToggle) sbToggle.textContent = '\u2699\ufe0f FILTROS';
            }
            if (!btnSairApres) {
                btnSairApres = document.createElement('button');
                btnSairApres.id = 'btn-sair-apresentacao';
                btnSairApres.textContent = '✕ SAIR';
                btnSairApres.addEventListener('click', sairApresentacao);
                mapInstance.getContainer().appendChild(btnSairApres);
            }
            btnSairApres.style.display = 'block';
            if (btnApres) btnApres.textContent = '✅ APRESENTAÇÃO ATIVA';
        }

        function sairApresentacao() {
            if (!modoApres) return;
            modoApres = false;
            document.body.classList.remove('modo-apresentacao');
            if (btnSairApres) btnSairApres.style.display = 'none';
            if (btnApres) btnApres.textContent = '⛶ MODO APRESENTAÇÃO';
        }

        if (btnApres) {
            btnApres.addEventListener('click', function () {
                if (modoApres) sairApresentacao();
                else entrarApresentacao();
            });
        }

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modoApres) sairApresentacao();
        });

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

        mapInstance.on('moveend', function () {
            atualizarMetricas();
        });

        atualizarMetricas();
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
