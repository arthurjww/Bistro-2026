(function(){
        "use strict";

        const svg = document.getElementById('mapa');
        const NS = 'http://www.w3.org/2000/svg';

        function el(tag, attrs = {}) {
            const node = document.createElementNS(NS, tag);
            Object.entries(attrs).forEach(([key, value]) => {
                node.setAttribute(key, value);
            });
            return node;
        }

        /* O novo mapa foi desenhado em coordenadas da imagem (1280 x 853) */
        svg.setAttribute('viewBox', '0 0 1280 853');
        svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

        /* ---------- Geometria das mesas (novo mapa: salão único) ---------- */

    const allTables = [
        { id: 'tA', type: 'round', cx: 640, cy: 225, r: 28, seats: 6, label: 'Mesa A', salao: 1 },
        { id: 'tB', type: 'round', cx: 528, cy: 180, r: 28, seats: 6, label: 'Mesa B', salao: 1 },
        { id: 'tC', type: 'round', cx: 412, cy: 165, r: 28, seats: 6, label: 'Mesa C', salao: 1 },
        { id: 'tD', type: 'round', cx: 298, cy: 195, r: 28, seats: 6, label: 'Mesa D', salao: 1 },
        { id: 'tE', type: 'round', cx: 195, cy: 250, r: 28, seats: 6, label: 'Mesa E', salao: 1 },
        { id: 'tF', type: 'round', cx: 285, cy: 330, r: 28, seats: 6, label: 'Mesa F', salao: 1 },
        { id: 'tG', type: 'round', cx: 625, cy: 350, r: 28, seats: 6, label: 'Mesa G', salao: 1 },
        { id: 'tH', type: 'round', cx: 480, cy: 310, r: 28, seats: 6, label: 'Mesa H', salao: 1 },
        { id: 'tI', type: 'round', cx: 640, cy: 480, r: 28, seats: 6, label: 'Mesa I', salao: 1 },
        { id: 'tJ', type: 'round', cx: 500, cy: 480, r: 28, seats: 6, label: 'Mesa J', salao: 1 },
        { id: 'tK', type: 'round', cx: 365, cy: 450, r: 28, seats: 6, label: 'Mesa K', salao: 1 },
        { id: 'tL', type: 'round', cx: 210, cy: 455, r: 28, seats: 6, label: 'Mesa L', salao: 1 },
        { id: 'tM', type: 'round', cx: 330, cy: 585, r: 28, seats: 6, label: 'Mesa M', salao: 1 },
        { id: 'tN', type: 'round', cx: 195, cy: 610, r: 28, seats: 6, label: 'Mesa N', salao: 1 },
    ];

        const SEAT_SIZE = 14;
        const API_BASE = '';
        const saloesDisponiveis = new Set(JSON.parse(svg.dataset.saloes || '[1, 2]'));
        const tables = allTables.filter(table => saloesDisponiveis.has(table.salao));
        const queryParams = new URLSearchParams(window.location.search);
        let diaBistro = queryParams.get('dia');
        let MAPA_ENDPOINT = '';
        const diaBistroSelect = document.getElementById('diaBistroSelect');

        function getSeatPositions(t) {

            const seats = [];

            if (t.type === 'round') {

                const start = -Math.PI / 2;
                const dist = t.r + 14;

                for (let i = 0; i < t.seats; i++) {
                    const a = start + 2 * Math.PI * i / t.seats;
                    seats.push({
                        id: `${t.id}-s${i + 1}`,
                        x: t.cx + dist * Math.cos(a),
                        y: t.cy + dist * Math.sin(a)
                    });
                }

            } else if (t.type === 'vert') {

                const n = t.seats / 2;
                const usable = t.h - 28;

                for (let i = 0; i < n; i++) {
                    const y = t.cy - t.h / 2 + 14 + usable * i / (n - 1);
                    seats.push({ id: `${t.id}-s${i + 1}`, x: t.cx - t.w / 2 - 15, y });
                }

                for (let i = 0; i < n; i++) {
                    const y = t.cy - t.h / 2 + 14 + usable * i / (n - 1);
                    seats.push({ id: `${t.id}-s${n + i + 1}`, x: t.cx + t.w / 2 + 15, y });
                }

            } else {

                const top = Math.ceil(t.seats / 2);
                const bot = t.seats - top;
                const margin = 18;
                const usable = t.w - 2 * margin;
                const off = 15;

                for (let i = 0; i < top; i++) {
                    const x = t.cx - t.w / 2 + margin + (top > 1 ? usable * i / (top - 1) : usable / 2);
                    seats.push({ id: `${t.id}-s${i + 1}`, x, y: t.cy - t.h / 2 - off });
                }

                for (let i = 0; i < bot; i++) {
                    const x = t.cx - t.w / 2 + margin + (bot > 1 ? usable * i / (bot - 1) : usable / 2);
                    seats.push({ id: `${t.id}-s${top + i + 1}`, x, y: t.cy + t.h / 2 + off });
                }

            }

            return seats;
        }

        const seatToTable = {};
        tables.forEach(t => getSeatPositions(t).forEach(s => { seatToTable[s.id] = t.id; }));
        const allSeatIds = Object.keys(seatToTable);
        const TOTAL_SEATS = allSeatIds.length;

        function getLugarCode(seatId) {
            const tableId = seatToTable[seatId];
            const table = tables.find(t => t.id === tableId);
            const seatNumber = seatId.substring(seatId.indexOf('-s') + 2);
            return `${table.label.replace('Mesa ', '')}${seatNumber}`;
        }

        const seatIdByLugarCode = new Map(allSeatIds.map(id => [getLugarCode(id), id]));
        const lugaresIndisponiveisPorRegra = new Set(
            allSeatIds.filter(id => getLugarCode(id).startsWith('H'))
        );

        /* ---------- Planta fixa: paredes, portas, bar, banheiros, etc. ---------- */

        const INK = '#111';
        const BG = '#fff';

        function path(d, attrs = {}) {
            const p = el('path', { d, ...attrs });
            svg.appendChild(p);
            return p;
        }

        /* Parede dupla (traço preto largo + traço branco por cima) */
        function wall(d) {
            path(d, { style: `fill:none;stroke:${INK};stroke-width:9;stroke-linejoin:miter;stroke-linecap:butt;` });
            path(d, { style: `fill:none;stroke:${BG};stroke-width:4;stroke-linejoin:miter;stroke-linecap:butt;` });
        }

        function line(x1, y1, x2, y2, w = 2, color = INK) {
            svg.appendChild(el('line', { x1, y1, x2, y2, style: `stroke:${color};stroke-width:${w};` }));
        }

        function box(x, y, w, h, style = '') {
            svg.appendChild(el('rect', {
                x, y, width: w, height: h,
                style: `fill:${BG};stroke:${INK};stroke-width:2;${style}`
            }));
        }

        function txt(x, y, content, size = 16, weight = 600, extra = '') {
            const t = el('text', {
                x, y,
                style: `font-family:Inter,Arial,sans-serif;font-size:${size}px;font-weight:${weight};fill:${INK};text-anchor:middle;${extra}`
            });
            t.textContent = content;
            svg.appendChild(t);
            return t;
        }

        function arrowHead(x, y, angleRad, size = 10) {
            const a1 = angleRad + Math.PI - 0.4;
            const a2 = angleRad + Math.PI + 0.4;
            svg.appendChild(el('polygon', {
                points: `${x},${y} ${x + size * Math.cos(a1)},${y + size * Math.sin(a1)} ${x + size * Math.cos(a2)},${y + size * Math.sin(a2)}`,
                style: `fill:${INK};`
            }));
        }

        // Fundo branco da planta
        svg.appendChild(el('rect', { x: 0, y: 0, width: 1280, height: 853, rx: 8, style: `fill:${BG};` }));

        // Paredes do salão principal (lado esquerdo, topo com janelas, até o banheiro)
        wall('M 110 320 L 110 175 L 220 175 L 220 160 L 258 135 L 335 95 L 395 92 L 530 92 L 610 100 L 700 160 L 712 164 L 912 170');
        // Parede esquerda abaixo da porta e piso inferior até a escada
        wall('M 110 362 L 110 697 L 390 693 L 390 768 L 460 768 L 460 572');
        // Bar / área de retiros
        wall('M 460 572 L 820 578 L 820 660 L 910 660');
        // Cozinha: parede inferior até a área coberta
        wall('M 1015 665 L 1015 690 L 1252 690 L 1252 330 L 1112 330');
        // Banheiros
        wall('M 912 335 L 912 122 L 1238 122 L 1238 330 L 1112 330');
        wall('M 905 335 L 1062 333');

        // Janela do banheiro e da parede esquerda
        box(906, 205, 10, 60, 'stroke-width:1.5;');
        box(107, 255, 12, 63, 'stroke-width:1.5;');
        box(168, 170, 10, 12, 'stroke-width:1.5;');
        box(106, 418, 12, 10, 'stroke-width:1.5;');

        // Janelas (marcas ao longo da parede do topo)
        [[262, 134, -35], [320, 100, -35], [395, 95, 0], [462, 92, 0], [528, 93, 0], [612, 105, 35]].forEach(([x, y, a]) => {
            svg.appendChild(el('rect', {
                x: x - 4, y: y - 9, width: 8, height: 18,
                transform: `rotate(${a} ${x} ${y})`,
                style: `fill:${BG};stroke:${INK};stroke-width:1.5;`
            }));
        });
        path('M 262 144 L 322 106', { style: `fill:none;stroke:${INK};stroke-width:1.5;` });
        path('M 396 103 L 528 103', { style: `fill:none;stroke:${INK};stroke-width:1.5;` });
        path('M 614 114 L 694 164', { style: `fill:none;stroke:${INK};stroke-width:1.5;` });

        // JANELAS + setas
        txt(404, 60, 'JANELAS', 16, 500);
        line(360, 62, 325, 92, 1.5);
        arrowHead(320, 96, Math.atan2(96 - 62, 320 - 360));
        line(460, 55, 505, 60, 1.5);
        line(505, 60, 513, 84, 1.5);
        arrowHead(514, 88, Math.PI / 2);

        // Porta lateral esquerda
        line(112, 322, 112, 360, 2);
        line(112, 360, 150, 360, 2);
        path('M 150 360 A 38 38 0 0 0 112 322', { style: `fill:none;stroke:${INK};stroke-width:2;` });
        txt(46, 324, 'PORTA', 14, 500);
        line(80, 320, 106, 320, 1.5);
        arrowHead(108, 320, 0, 8);

        // Palco / músicos
        box(706, 187, 168, 79);
        txt(793, 231, 'MÚSICOS', 15, 600);

        // Banheiros
        txt(1077, 234, 'BANHEIROS', 34, 500, 'font-family:Arial,sans-serif;');
        line(1060, 285, 1060, 330, 2);
        path('M 978 330 A 82 45 0 0 1 1058 285', { style: `fill:none;stroke:${INK};stroke-width:2;` });

        // Área de jantar
        txt(393, 362, 'ÁREA', 14, 600);
        txt(393, 383, 'DE JANTAR', 14, 600);

        // Escada
        box(412, 574, 42, 190, 'stroke-width:2;');
        for (let y = 590; y < 762; y += 16) {
            line(412, y, 454, y, 1.5);
        }

        // Bar / área de retiros (janelas do balcão)
        box(575, 578, 230, 22, 'stroke-width:1.5;');
        [647, 698, 748].forEach(x => line(x, 574, x, 604, 2));
        txt(655, 647, 'BAR / ÁREA', 14, 600);
        txt(655, 669, 'DE RETIROS', 14, 600);

        // Cozinha
        txt(932, 716, 'Cozinha', 32, 400, 'font-family:Arial,sans-serif;');
        line(1012, 617, 1012, 664, 2);
        path('M 932 662 A 82 47 0 0 1 1012 617', { style: `fill:none;stroke:${INK};stroke-width:2;` });

        // Balcão em L (área coberta)
        svg.appendChild(el('rect', { x: 1077, y: 345, width: 153, height: 33, style: 'fill:#3b3f2f;' }));
        svg.appendChild(el('rect', { x: 1195, y: 345, width: 35, height: 135, style: 'fill:#3b3f2f;' }));

        // Pilar
        svg.appendChild(el('circle', { cx: 1094, cy: 631, r: 22, style: 'fill:#3b3f2f;' }));

        // Porta de entrada + seta
        txt(1085, 414, 'PORTA', 14, 600);
        txt(1085, 436, 'ENTRADA', 14, 600);
        line(1118, 455, 1228, 530, 2.5);
        arrowHead(1238, 537, Math.atan2(537 - 455, 1238 - 1118), 14);
        txt(1135, 522, 'ÁREA', 15, 600);
        txt(1135, 544, 'COBERTA', 15, 600);
        line(1170, 562, 1245, 562, 2);
        line(1245, 562, 1245, 645, 2);
        path('M 1170 562 A 75 83 0 0 0 1245 645', { style: `fill:none;stroke:${INK};stroke-width:2;` });

        /* ---------- Desenho das mesas e cadeiras ---------- */

        const seatEls = {};

        tables.forEach(t => {

            const tg = el('g', { class: 'table-group', 'data-table': t.id });

            tg.appendChild(
                t.type === 'round'
                    ? el('circle', { cx: t.cx, cy: t.cy, r: t.r, class: 'table-shape', style: `fill:${BG};stroke:${INK};stroke-width:2;` })
                    : el('rect', { x: t.cx - t.w / 2, y: t.cy - t.h / 2, width: t.w, height: t.h, rx: 8, class: 'table-shape', style: `fill:${BG};stroke:${INK};stroke-width:2;` })
            );

            const lbl = el('text', {
                x: t.cx, y: t.cy + 10,
                class: 'table-label',
                style: 'font-family:Arial,sans-serif;font-size:30px;font-weight:700;fill:#d71920;text-anchor:middle;'
            });
            lbl.textContent = t.label.replace('Mesa ', '');
            tg.appendChild(lbl);

            svg.appendChild(tg);
            getSeatPositions(t).forEach(s => {

                const r = el('rect', {
                    x: s.x - SEAT_SIZE / 2,
                    y: s.y - SEAT_SIZE / 2,
                    width: SEAT_SIZE,
                    height: SEAT_SIZE,
                    rx: 3,
                    class: 'seat st-available',
                    'data-id': s.id
                });

                const title = el('title', {});
                title.textContent = getLugarCode(s.id).startsWith('H')
                    ? `${t.label} — cadeira ${s.id.split('-s')[1]} (indisponível)`
                    : `${t.label} — cadeira ${s.id.split('-s')[1]}`;
                r.appendChild(title);

                svg.appendChild(r);
                seatEls[s.id] = r;

                r.addEventListener('click', (e) => {
                    e.stopPropagation();
                    onSeatClick(s.id);
                });

            });

        });

        /* ---------- Estado ---------- */

        let reservedSet = new Set(lugaresIndisponiveisPorRegra);
        let pendingSet = new Set();
        let codigoConfirmado = false;
        let usosRestantes = Number(document.body.dataset.usosRestantes || 0);

        function repaintSeats() {

            allSeatIds.forEach(id => {

                const r = seatEls[id];
                const isPending = pendingSet.has(id);
                const isReserved = reservedSet.has(id);

                r.setAttribute(
                    'class',
                    'seat ' + (isPending ? 'st-selected' : isReserved ? 'st-reserved' : 'st-available')
                );

                r.style.fill = isPending ? 'var(--selected)' : isReserved ? 'var(--reserved)' : 'var(--available)';
                r.style.stroke = isPending ? '#8a6a0f' : isReserved ? 'var(--reserved-line)' : 'var(--available-line)';
                r.style.strokeWidth = '1.3';
            });

            document.getElementById('occNum').textContent = TOTAL_SEATS - reservedSet.size;

            const info = document.getElementById('selectionInfo');
            info.innerHTML = pendingSet.size === 0
                ? 'Nenhuma cadeira selecionada'
                : `<b>${pendingSet.size}</b> cadeira(s) selecionada(s)`;

            document.getElementById('confirmBtn').disabled = pendingSet.size === 0;

        }

        function onSeatClick(id) {

            if (reservedSet.has(id)) {
                showToast('Esse lugar está indisponível.');
                return;
            }

            if(!codigoConfirmado) {
                setCodeStatus('Valide o código do aluno antes de escolher lugares', 'error');
                codeInput.focus();
                return;
            }

            if (!pendingSet.has(id) && pendingSet.size >= usosRestantes) {
                showToast(`Você só pode selecionar ${usosRestantes} lugar(es).`);
                return;

            }

            if (pendingSet.has(id)) {
                pendingSet.delete(id);
            } else {
                pendingSet.add(id);
            }

            repaintSeats();
        }

        /* ---------- Limpar seleção ---------- */

        document.getElementById('clearBtn').addEventListener('click', () => {
            pendingSet.clear();
            repaintSeats();
        });

        /* ---------- Código do aluno ---------- */

        const codeInput = document.getElementById('codigoInput');
        const codeStatus = document.getElementById('codeStatus');

        function setCodeStatus(message, type = '') {
            codeStatus.textContent = message;
            codeStatus.className = `code-status ${type}`.trim();
        }

        document.getElementById('confirmCodeBtn').addEventListener('click', async () => {
            const codigo = codeInput.value.trim();

            if (codigo.length !== 6) {
                setCodeStatus('Digite o código de seis caracteres.', 'error');
                return;
            }

            try {
                const resposta = await fetch(
                    `${API_BASE}/lugares/confirmar_codigo?codigo=${encodeURIComponent(codigo)}`,
                    { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' }
                );
                const dados = await resposta.json();

                if (!resposta.ok) {
                    throw new Error(dados.erro || 'Não foi possível validar o código.');
                }

                codigoConfirmado = true;
                usosRestantes = dados.usos_restantes
                codeInput.disabled = true;
                document.getElementById('confirmCodeBtn').disabled = true;
                setCodeStatus(`${dados.usos_restantes} uso(s) restante(s).`, 'success');
            } catch (error) {
                codigoConfirmado = false;
                usosRestantes = 0;
                setCodeStatus(error.message, 'error');
            }
        });

        /* ---------- Confirmar (Próximo) ---------- */

        document.getElementById('confirmBtn').addEventListener('click', async () => {

            if (pendingSet.size === 0) return;

            if (!codigoConfirmado) {
                setCodeStatus('Valide o código do aluno antes de reservar.', 'error');
                codeInput.focus();
                return;
            }

            const selectedSeats = Array.from(pendingSet);
            const confirmedSeats = [];

            try {
                for (const seatId of selectedSeats) {
                    const codLugar = getLugarCode(seatId);
                    const resposta = await fetch(
                        `${API_BASE}/lugares/${encodeURIComponent(codLugar)}/escolher?dia=${encodeURIComponent(diaBistro)}`,
                        {
                            method: 'POST',
                            headers: { 'Accept': 'application/json' },
                            credentials: 'same-origin'
                        }
                    );

                    const dados = await resposta.json();
                    if (!resposta.ok) {
                        throw new Error(dados.erro || 'Não foi possível reservar o lugar.');
                    }

                    confirmedSeats.push(seatId);
                }

                confirmedSeats.forEach(id => {
                    reservedSet.add(id);
                    pendingSet.delete(id);
                });
                repaintSeats();
                repaintSeats();
                showToast('Lugares reservados. Continuando para o pagamento.');
                window.location.assign(`${API_BASE}/lugares/seguir`);
            } catch (error) {
                confirmedSeats.forEach(id => {
                    reservedSet.add(id);
                    pendingSet.delete(id);
                });
                repaintSeats();
                repaintSeats();
                showToast(error.message);
            }

        });

        /* ---------- Toast ---------- */

        let toastTimer;

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            clearTimeout(toastTimer);
            toastTimer = setTimeout(() => t.classList.remove('show'), 3200);
        }

        /* ---------- Sincronização com o Flask ---------- */

        async function atualizarMapa({ silencioso = false } = {}) {
            try {
                const resposta = await fetch(MAPA_ENDPOINT, {
                    headers: { 'Accept': 'application/json' },
                    credentials: 'same-origin'
                });
                const dados = await resposta.json().catch(() => ({}));

                if (!resposta.ok) {
                    throw new Error(dados.erro || 'Não foi possível carregar o mapa.');
                }

                if (!Array.isArray(dados.lugares)) {
                    throw new Error('O mapa recebido do servidor é inválido.');
                }

                const novasReservas = new Set(
                    dados.lugares
                        .filter(lugar => Number(lugar.ocupado) !== 0)
                        .map(lugar => seatIdByLugarCode.get(lugar.cod_lugar))
                        .filter(Boolean)
                );
                lugaresIndisponiveisPorRegra.forEach(id => novasReservas.add(id));
                const selecoesIndisponiveis = [...pendingSet].filter(id => novasReservas.has(id));

                selecoesIndisponiveis.forEach(id => pendingSet.delete(id));
                reservedSet = novasReservas;
                repaintSeats();

                if (selecoesIndisponiveis.length && !silencioso) {
                    showToast('Uma cadeira selecionada acabou de ficar indisponível.');
                }
            } catch (error) {
                if (!silencioso) {
                    showToast(error.message);
                }
            }
        }

        /* ---------- Init ---------- */

        function formatarData(data) {
            const [ano, mes, dia] = data.split('-');
            return `${dia}/${mes}/${ano}`;
        }

        async function carregarDatas() {
            const resposta = await fetch(`${API_BASE}/lugares/datas`, {
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin'
            });
            const dados = await resposta.json().catch(() => ({}));

            if (!resposta.ok || !Array.isArray(dados.datas) || !dados.datas.length) {
                throw new Error(dados.erro || 'Nenhuma data do bistrô foi configurada.');
            }

            diaBistroSelect.replaceChildren();
            dados.datas.forEach(data => {
                const option = document.createElement('option');
                option.value = data;
                option.textContent = formatarData(data);
                diaBistroSelect.appendChild(option);
            });

            if (!dados.datas.includes(diaBistro)) {
                diaBistro = dados.datas[0];
                const url = new URL(window.location.href);
                url.searchParams.set('dia', diaBistro);
                window.history.replaceState({}, '', url);
            }

            diaBistroSelect.value = diaBistro;
            MAPA_ENDPOINT = `${API_BASE}/lugares/mapa?dia=${encodeURIComponent(diaBistro)}`;
        }

        diaBistroSelect.addEventListener('change', () => {
            const url = new URL(window.location.href);
            url.searchParams.set('dia', diaBistroSelect.value);
            window.location.assign(url);
        });
        
        async function liberarReservasAntesDoMapa() {
            const resposta = await fetch(`${API_BASE}/lugares/liberar-reservas`, {
                method: 'POST',
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin'
            });

            const dados = await resposta.json().catch(() => ({}));

            if (!resposta.ok) {
                throw new Error(dados.erro || 'Não foi possível liberar as reservas.');
            }
        }
        async function init() {
            await liberarReservasAntesDoMapa()
            await carregarDatas();
            repaintSeats();
            await atualizarMapa();
            window.setInterval(() => atualizarMapa({ silencioso: true }), 15000);
        }

        init().catch(error => showToast(error.message));

        window.addEventListener('pageshow', event => {
            if (event.persisted) {
                init().catch(error => showToast(error.message));
            }
        });

    })();
