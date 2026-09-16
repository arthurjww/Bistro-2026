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

        /* ---------- Geometria das mesas (Salão 1 + Salão 2) ---------- */

        const allTables = [

            /* Salão 1 (direita) */
            { id: 'tG', type: 'rect',  cx: 730,  cy: 110, w: 210, h: 54, seats: 8,  label: 'Mesa G' },
            { id: 'tF', type: 'rect',  cx: 730,  cy: 260, w: 210, h: 54, seats: 8,  label: 'Mesa F' },
            { id: 'tE', type: 'rect',  cx: 730,  cy: 410, w: 210, h: 54, seats: 8,  label: 'Mesa E' },
            { id: 'tD', type: 'rect',  cx: 730,  cy: 555, w: 210, h: 54, seats: 8,  label: 'Mesa D' },
            { id: 'tH', type: 'rect',  cx: 1000, cy: 110, w: 170, h: 54, seats: 6,  label: 'Mesa H' },
            { id: 'tI', type: 'rect',  cx: 1000, cy: 260, w: 170, h: 54, seats: 6,  label: 'Mesa I' },
            { id: 'tJ', type: 'vert',  cx: 1000, cy: 410, w: 64,  h: 140, seats: 6, label: 'Mesa J' },
            { id: 'tK', type: 'round', cx: 1150, cy: 410, r: 50, seats: 6,          label: 'Mesa K' },
            { id: 'tC', type: 'round', cx: 740,  cy: 705, r: 52, seats: 8,          label: 'Mesa C' },
            { id: 'tB', type: 'round', cx: 940,  cy: 640, r: 46, seats: 6,          label: 'Mesa B' },
            { id: 'tA', type: 'round', cx: 1150, cy: 705, r: 52, seats: 8,          label: 'Mesa A' },

            /* Salão 2 (esquerda) */
            { id: 'tP', type: 'vert',  cx: 130,  cy: 490, w: 60,  h: 140, seats: 8, label: 'Mesa P' },
            { id: 'tL', type: 'round', cx: 390,  cy: 480, r: 50, seats: 6,          label: 'Mesa L' },
            { id: 'tO', type: 'vert',  cx: 130,  cy: 680, w: 60,  h: 140, seats: 6, label: 'Mesa O' },
            { id: 'tN', type: 'rect',  cx: 270,  cy: 680, w: 70,  h: 90,  seats: 6, label: 'Mesa N' },
            { id: 'tM', type: 'round', cx: 390,  cy: 680, r: 46, seats: 6,          label: 'Mesa M' },
        ];

        const SEAT_SIZE = 16;
        const API_BASE = '';
        const saloesDisponiveis = new Set(JSON.parse(svg.dataset.saloes || '[1, 2]'));
        const tables = allTables.filter(table => {
            const salao = 'ABCDEFGHIJK'.includes(table.id[1]) ? 1 : 2;
            return saloesDisponiveis.has(salao);
        });
        const queryParams = new URLSearchParams(window.location.search);
        const hoje = new Date();
        const dataLocal = [
            hoje.getFullYear(),
            String(hoje.getMonth() + 1).padStart(2, '0'),
            String(hoje.getDate()).padStart(2, '0')
        ].join('-');
        const diaBistro = queryParams.get('dia') || dataLocal;
        const MAPA_ENDPOINT = `${API_BASE}/lugares/mapa?dia=${encodeURIComponent(diaBistro)}`;

        function getSeatPositions(t) {

            const seats = [];

            if (t.type === 'round') {

                const start = -Math.PI / 2;
                const dist = t.r + 16;

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

        /* ---------- Planta fixa: paredes, salões, corredor, entrada, fixtures ---------- */

        // Parede do Salão 1
        svg.appendChild(el('rect', { x: 515, y: 35, width: 950, height: 790, rx: 4, class: 'wall' }));
        {
            const t = el('text', { x: 540, y: 64, style: 'font-family:Fraunces,serif;font-size:16px;font-weight:600;fill:var(--text-light,#fff);' });
            t.textContent = 'Salão 1';
            svg.appendChild(t);
        }

        // Parede do Salão 2
        svg.appendChild(el('rect', { x: 35, y: 375, width: 450, height: 450, rx: 4, class: 'wall' }));
        {
            const t = el('text', { x: 60, y: 404, style: 'font-family:Fraunces,serif;font-size:16px;font-weight:600;fill:var(--text-light,#fff);' });
            t.textContent = 'Salão 2';
            svg.appendChild(t);
        }

        // Corredor de ligação entre os salões
        {
            svg.appendChild(el('rect', { x: 485, y: 535, width: 30, height: 170, class: 'fixture' }));
            const t = el('text', {
                x: 500, y: 620, transform: 'rotate(-90 500 620)',
                style: 'font-family:Inter,sans-serif;font-size:11px;fill:var(--text-muted,#b8b8b8);text-anchor:middle;'
            });
            t.textContent = 'Circulação entre os salões';
            svg.appendChild(t);
        }

        // Seta + rótulo da entrada
        {
            svg.appendChild(el('polygon', {
                points: '260,838 232,878 288,878',
                style: 'fill:var(--brass-soft,#a13343);'
            }));
            const t1 = el('text', {
                x: 260, y: 898,
                style: 'font-family:Inter,sans-serif;font-size:12px;font-weight:700;fill:var(--text-light,#fff);text-anchor:middle;'
            });
            t1.textContent = 'ENTRADA PARA OS SALÕES';
            const t2 = el('text', {
                x: 260, y: 914,
                style: 'font-family:Inter,sans-serif;font-size:12px;font-weight:700;fill:var(--text-light,#fff);text-anchor:middle;'
            });
            t2.textContent = 'DO RESTAURANTE';
            svg.appendChild(t1);
            svg.appendChild(t2);
        }

        // Toaletes
        svg.appendChild(el('rect', { x: 1250, y: 55, width: 170, height: 120, rx: 8, class: 'fixture' }));
        {
            const t = el('text', { x: 1335, y: 120, class: 'fixture-label' });
            t.textContent = 'TOALETES';
            svg.appendChild(t);
        }

        // Palco
        svg.appendChild(el('rect', { x: 850, y: 750, width: 200, height: 55, rx: 8, class: 'fixture' }));
        {
            const t = el('text', { x: 950, y: 782, class: 'fixture-label' });
            t.textContent = 'PALCO';
            svg.appendChild(t);
        }

        // Cozinha
        svg.appendChild(el('rect', { x: 1400, y: 330, width: 45, height: 380, rx: 5, class: 'fixture' }));
        {
            const t = el('text', { x: 1422, y: 525, transform: 'rotate(-90 1422 525)', class: 'fixture-label' });
            t.textContent = 'COZINHA';
            svg.appendChild(t);
        }

        /* ---------- Desenho das mesas e cadeiras ---------- */

        const seatEls = {};
        const tableGroupEls = {};

        tables.forEach(t => {

            const tg = el('g', { class: 'table-group', 'data-table': t.id });

            tg.appendChild(
                t.type === 'round'
                    ? el('circle', { cx: t.cx, cy: t.cy, r: t.r, class: 'table-shape' })
                    : el('rect', { x: t.cx - t.w / 2, y: t.cy - t.h / 2, width: t.w, height: t.h, rx: 8, class: 'table-shape' })
            );

            const lbl = el('text', { x: t.cx, y: t.cy - 3, class: 'table-label' });
            lbl.textContent = t.label;
            tg.appendChild(lbl);

            const cap = el('text', { x: t.cx, y: t.cy + 10, class: 'table-cap' });
            cap.textContent = t.seats + ' lugares';
            tg.appendChild(cap);

            tg.addEventListener('click', () => selectTable(t.id));

            svg.appendChild(tg);
            tableGroupEls[t.id] = tg;

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
                title.textContent = `${t.label} — cadeira ${s.id.split('-s')[1]}`;
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

        let reservedSet = new Set();
        let pendingSet = new Set();
        let activeTableId = null;
        let codigoConfirmado = false;

        function tableFreeCount(tableId) {
            const seats = allSeatIds.filter(id => seatToTable[id] === tableId);
            return seats.filter(id => !reservedSet.has(id)).length;
        }

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
                r.style.opacity = (activeTableId && seatToTable[id] !== activeTableId) ? '0.55' : '1';

            });

            document.getElementById('occNum').textContent = TOTAL_SEATS - reservedSet.size;

            const info = document.getElementById('selectionInfo');
            info.innerHTML = pendingSet.size === 0
                ? 'Nenhuma cadeira selecionada'
                : `<b>${pendingSet.size}</b> cadeira(s) selecionada(s)`;

            document.getElementById('confirmBtn').disabled = pendingSet.size === 0;

            renderTableList();
        }

        function onSeatClick(id) {

            if (reservedSet.has(id)) {
                showToast('Essa cadeira já foi comprada.');
                return;
            }

            activeTableId = seatToTable[id];

            if (pendingSet.has(id)) {
                pendingSet.delete(id);
            } else {
                pendingSet.add(id);
            }

            repaintSeats();
            highlightActiveTable();
        }

        function selectTable(id) {
            activeTableId = id;
            repaintSeats();
            highlightActiveTable();
        }

        function highlightActiveTable() {

            Object.keys(tableGroupEls).forEach(id => {
                tableGroupEls[id].classList.toggle('active', id === activeTableId);
            });

            const box = document.getElementById('selectedTableLabel');
            const sub = document.getElementById('selectedTableSub');

            if (!activeTableId) {
                box.textContent = 'Nenhuma';
                sub.textContent = 'Escolha uma mesa para começar.';
                return;
            }

            const t = tables.find(x => x.id === activeTableId);
            const free = tableFreeCount(activeTableId);

            box.textContent = t.label;
            sub.textContent = `${free} de ${t.seats} lugares livres`;
        }

        function renderTableList() {

            const list = document.getElementById('tableList');
            list.innerHTML = '';

            const sortedTables = [...tables].sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'));

            sortedTables.forEach(t => {

                const free = tableFreeCount(t.id);

                const btn = document.createElement('button');
                btn.className = 'table-btn' + (t.id === activeTableId ? ' active' : '');

                btn.innerHTML = `
                    <span>
                        <span class="tname">${t.label}</span>
                        <span class="tcap">${t.seats} lugares</span>
                    </span>
                    <span class="tfree${free === 0 ? ' full' : ''}">
                        ${free === 0 ? 'lotada' : free + ' livre' + (free === 1 ? '' : 's')}
                    </span>
                `;

                btn.addEventListener('click', () => selectTable(t.id));

                list.appendChild(btn);
            });
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
                codeInput.disabled = true;
                document.getElementById('confirmCodeBtn').disabled = true;
                setCodeStatus(`${dados.usos_restantes} uso(s) restante(s).`, 'success');
            } catch (error) {
                codigoConfirmado = false;
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
                highlightActiveTable();
                showToast('Lugares reservados. Continuando para o pagamento.');
                window.location.assign(`${API_BASE}/lugares/seguir`);
            } catch (error) {
                confirmedSeats.forEach(id => {
                    reservedSet.add(id);
                    pendingSet.delete(id);
                });

                repaintSeats();
                highlightActiveTable();
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
                const selecoesIndisponiveis = [...pendingSet].filter(id => novasReservas.has(id));

                selecoesIndisponiveis.forEach(id => pendingSet.delete(id));
                reservedSet = novasReservas;
                repaintSeats();
                highlightActiveTable();

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

        async function init() {
            repaintSeats();
            highlightActiveTable();
            await atualizarMapa();
            window.setInterval(() => atualizarMapa({ silencioso: true }), 15000);
        }

        init();

    })();
