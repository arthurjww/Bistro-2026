/* ==================================================================
   INGRESSOS — Sinestesia (front-end estático)

   - Sem IDs no HTML: tudo é selecionado pelos atributos data-js.
   - Sem variáveis de ambiente (.env) e sem localStorage/sessionStorage:
     os dados passam de uma página para a outra pela própria URL.
   - O link de cada QR code é montado a partir do endereço atual da
     página, então funciona em qualquer domínio onde o site for publicado.

   Fluxo:
   ingressos.html → info_ingressos.html → pagamento.html → confirmacao.html
                                                              ↓ (QR code)
                                                         ingresso.html
   ================================================================== */

(function () {
    'use strict';

    /* ------------------------- Configuração ------------------------- */

    // Preços em reais (lorem ipsum — definir os valores reais depois)
    const PRECOS = {
        ADULTO: 0,
        CRIANCA: 0
    };

    const NOMES_TIPO = { ADULTO: 'ADULTO', CRIANCA: 'CRIANÇA' };
    const MAX_INGRESSOS = 10;

    // Sem 0/O e 1/I para evitar confusão na leitura do código
    const ALFABETO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const FORMATO_CODIGO = /^SNT-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;

    /* -------------------------- Utilitários -------------------------- */

    function el(nome, raiz) {
        return (raiz || document).querySelector('[data-js="' + nome + '"]');
    }

    function els(nome, raiz) {
        return Array.from((raiz || document).querySelectorAll('[data-js="' + nome + '"]'));
    }

    // Sempre textContent (nunca innerHTML) para dados digitados pelo usuário
    function texto(nome, valor, raiz) {
        els(nome, raiz).forEach(function (alvo) {
            alvo.textContent = valor;
        });
    }

    function moeda(valor) {
        return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function inteiro(valor, min, max, padrao) {
        const n = parseInt(valor, 10);
        if (isNaN(n)) return padrao;
        return Math.min(max, Math.max(min, n));
    }

    function tipoValido(tipo) {
        return tipo === 'CRIANCA' ? 'CRIANCA' : 'ADULTO';
    }

    function contar(tipos) {
        const contagem = { ADULTO: 0, CRIANCA: 0 };
        tipos.forEach(function (tipo) { contagem[tipo] += 1; });
        return contagem;
    }

    function totalDe(contagem) {
        return contagem.ADULTO * PRECOS.ADULTO + contagem.CRIANCA * PRECOS.CRIANCA;
    }

    // Código aleatório criptograficamente seguro. Ex.: SNT-7K2Q-9XMD-4TPA
    function gerarCodigo(prefixo, grupos) {
        const bytes = new Uint8Array(grupos * 4);
        crypto.getRandomValues(bytes);

        const partes = [];
        for (let g = 0; g < grupos; g++) {
            let parte = '';
            for (let i = 0; i < 4; i++) {
                parte += ALFABETO[bytes[g * 4 + i] % ALFABETO.length];
            }
            partes.push(parte);
        }
        return prefixo + '-' + partes.join('-');
    }

    // Lê da URL os participantes: qtd, nome_N, email_N, tipo_N, obs_N, cod_N
    function lerCompra(params) {
        const qtd = inteiro(params.get('qtd'), 0, MAX_INGRESSOS, 0);
        const lista = [];

        for (let i = 1; i <= qtd; i++) {
            lista.push({
                indice: i,
                nome: (params.get('nome_' + i) || '').trim(),
                email: (params.get('email_' + i) || '').trim(),
                tipo: tipoValido(params.get('tipo_' + i)),
                obs: (params.get('obs_' + i) || '').trim(),
                codigo: (params.get('cod_' + i) || '').trim().toUpperCase()
            });
        }
        return lista;
    }

    function preencherPrecos() {
        els('preco').forEach(function (alvo) {
            alvo.textContent = moeda(PRECOS[alvo.dataset.tipo] || 0);
        });
    }

    function atualizarResumo(contagem) {
        ['ADULTO', 'CRIANCA'].forEach(function (tipo) {
            texto('qtd-' + tipo, contagem[tipo]);
            texto('subtotal-' + tipo, moeda(contagem[tipo] * PRECOS[tipo]));
        });
        texto('total', moeda(totalDe(contagem)));
    }

    function mostrarSemDados() {
        const aviso = el('sem-dados');
        const conteudo = el('conteudo');
        if (aviso) aviso.hidden = false;
        if (conteudo) conteudo.hidden = true;
    }

    // Desenha o QR code (SVG) usando a biblioteca js/vendor/qrcode.js
    function desenharQR(alvo, conteudo) {
        if (!alvo || typeof qrcode !== 'function') return;

        const qr = qrcode(0, 'M');
        qr.addData(conteudo);
        qr.make();

        alvo.innerHTML = qr.createSvgTag({ cellSize: 4, scalable: true });
        alvo.setAttribute('role', 'img');
        alvo.setAttribute('aria-label', 'QR code');
    }

    // URL absoluta da página do ingresso (é o conteúdo do QR code)
    function urlDoIngresso(ingresso, pedido) {
        const url = new URL('ingresso.html', window.location.href);
        url.search = new URLSearchParams({
            c: ingresso.codigo,
            n: ingresso.nome,
            e: ingresso.email,
            t: ingresso.tipo,
            o: ingresso.obs,
            p: pedido
        }).toString();
        return url.href;
    }

    function preencherBilhete(raiz, ingresso, pedido, url) {
        texto('tipo', NOMES_TIPO[ingresso.tipo], raiz);
        texto('nome', ingresso.nome, raiz);
        texto('email', ingresso.email || '—', raiz);
        texto('pedido', pedido || '—', raiz);
        texto('obs', ingresso.obs || 'Nenhuma observação informada.', raiz);
        texto('codigo', ingresso.codigo, raiz);
        desenharQR(el('qr', raiz), url);
    }

    /* -------------------- 01. Seleção de ingressos -------------------- */

    function paginaSelecao() {
        const params = new URLSearchParams(window.location.search);
        const form = el('form-selecao');
        const aviso = el('aviso');
        const entradas = Array.from(form.querySelectorAll('input[type="number"]'));

        // Ao voltar da etapa 2, mantém as quantidades escolhidas
        entradas.forEach(function (entrada) {
            if (params.has(entrada.name)) {
                entrada.value = inteiro(params.get(entrada.name), 0, MAX_INGRESSOS, 0);
            }
        });

        function atualizar() {
            const contagem = { ADULTO: 0, CRIANCA: 0 };
            entradas.forEach(function (entrada) {
                entrada.value = inteiro(entrada.value, 0, MAX_INGRESSOS, 0);
                contagem[entrada.dataset.tipo] = Number(entrada.value);
            });
            atualizarResumo(contagem);
            return contagem;
        }

        els('contador', form).forEach(function (contador) {
            const entrada = contador.querySelector('input');

            contador.addEventListener('click', function (evento) {
                const botao = evento.target.closest('button[data-acao]');
                if (!botao) return;

                const outros = entradas
                    .filter(function (outra) { return outra !== entrada; })
                    .reduce(function (soma, outra) { return soma + inteiro(outra.value, 0, MAX_INGRESSOS, 0); }, 0);

                const passo = botao.dataset.acao === 'mais' ? 1 : -1;
                const valor = inteiro(entrada.value, 0, MAX_INGRESSOS, 0) + passo;

                entrada.value = Math.max(0, Math.min(valor, MAX_INGRESSOS - outros));
                aviso.hidden = true;
                atualizar();
            });
        });

        entradas.forEach(function (entrada) {
            entrada.addEventListener('change', atualizar);
        });

        form.addEventListener('submit', function (evento) {
            const contagem = atualizar();
            const total = contagem.ADULTO + contagem.CRIANCA;

            if (total < 1 || total > MAX_INGRESSOS) {
                evento.preventDefault();
                aviso.textContent = total < 1
                    ? 'Selecione pelo menos 1 ingresso.'
                    : 'Máximo de ' + MAX_INGRESSOS + ' ingressos por compra.';
                aviso.hidden = false;
            }
        });

        atualizar();
    }

    /* ---------------------- 02. Participantes ---------------------- */

    function paginaParticipantes() {
        const params = new URLSearchParams(window.location.search);
        const form = el('form-participantes');
        const lista = el('lista-participantes');
        const modelo = el('modelo-participante');

        // Se veio do "editar" do pagamento, os dados já estão na URL
        const participantes = lerCompra(params);

        if (participantes.length === 0) {
            let adulto = inteiro(params.get('adulto'), 0, MAX_INGRESSOS, 1);
            let crianca = inteiro(params.get('crianca'), 0, MAX_INGRESSOS, 0);

            if (adulto + crianca === 0) adulto = 1;
            if (adulto + crianca > MAX_INGRESSOS) crianca = MAX_INGRESSOS - adulto;

            for (let i = 1; i <= adulto + crianca; i++) {
                participantes.push({
                    indice: i,
                    nome: '',
                    email: '',
                    tipo: i <= adulto ? 'ADULTO' : 'CRIANCA',
                    obs: ''
                });
            }
        }

        el('campo-qtd').value = participantes.length;

        // Gera um <details> para cada ingresso
        participantes.forEach(function (participante, posicao) {
            const copia = modelo.content.cloneNode(true);

            copia.querySelector('details').open = posicao === 0;
            texto('numero', participante.indice, copia);

            copia.querySelectorAll('[data-campo]').forEach(function (campo) {
                campo.name = campo.dataset.campo + '_' + participante.indice;

                if (campo.type === 'radio') {
                    campo.checked = campo.value === participante.tipo;
                } else {
                    campo.value = participante[campo.dataset.campo] || '';
                }
            });

            lista.appendChild(copia);
        });

        function atualizar() {
            const tipos = [];

            lista.querySelectorAll('details').forEach(function (details) {
                const marcado = details.querySelector('input[type="radio"]:checked');
                const tipo = marcado ? marcado.value : 'ADULTO';
                const nome = details.querySelector('[data-campo="nome"]').value.trim();

                tipos.push(tipo);
                texto('descricao', (nome || 'Preencha os dados do convidado') + ' · ' + NOMES_TIPO[tipo], details);
            });

            atualizarResumo(contar(tipos));
        }

        lista.addEventListener('input', atualizar);
        lista.addEventListener('change', atualizar);

        // Atalhos de restrições alimentares
        lista.addEventListener('click', function (evento) {
            const chip = evento.target.closest('[data-js="chip"]');
            if (!chip) return;

            const area = chip.closest('details').querySelector('textarea');
            const item = chip.textContent.replace('+', '').trim();
            const atual = area.value.trim();

            if (atual.toUpperCase().indexOf(item) !== -1) return;

            area.value = (atual ? atual + ', ' + item : item).slice(0, area.maxLength > 0 ? area.maxLength : 200);
        });

        // Abre o <details> que tiver campo inválido, para o navegador mostrar o erro
        form.addEventListener('invalid', function (evento) {
            const details = evento.target.closest('details');
            if (details) details.open = true;
        }, true);

        // Código do aluno
        const entradaCodigo = el('codigo-aluno-input');
        const botaoCodigo = el('codigo-aluno-enviar');
        const avisoCodigo = el('codigo-aluno-aviso');

        function aplicarCodigo(valor) {
            el('campo-codigo-aluno').value = valor;
            texto('resumo-codigo-valor', valor);
            el('resumo-codigo').hidden = !valor;
        }

        function mostrarAvisoCodigo(mensagem, sucesso) {
            avisoCodigo.textContent = mensagem;
            avisoCodigo.className = sucesso ? 'aviso sucesso' : 'aviso';
            avisoCodigo.hidden = false;
        }

        botaoCodigo.addEventListener('click', function () {
            const valor = entradaCodigo.value.trim().toUpperCase();

            if (!valor) {
                aplicarCodigo('');
                mostrarAvisoCodigo('Digite o código do aluno.', false);
                return;
            }

            if (!/^[A-Z0-9-]{3,30}$/.test(valor)) {
                aplicarCodigo('');
                mostrarAvisoCodigo('Código inválido. Use apenas letras, números e hífen.', false);
                return;
            }

            aplicarCodigo(valor);
            mostrarAvisoCodigo('Código ' + valor + ' aplicado. Lorem ipsum dolor sit amet.', true);
        });

        entradaCodigo.addEventListener('keydown', function (evento) {
            if (evento.key === 'Enter') {
                evento.preventDefault();
                botaoCodigo.click();
            }
        });

        const codigoDaUrl = (params.get('codigo_aluno') || '').trim().toUpperCase();
        if (codigoDaUrl) {
            entradaCodigo.value = codigoDaUrl;
            aplicarCodigo(codigoDaUrl);
        }

        // Voltar mantendo a quantidade
        const contagem = contar(participantes.map(function (p) { return p.tipo; }));
        els('voltar').forEach(function (link) {
            link.href = 'ingressos.html?adulto=' + contagem.ADULTO + '&crianca=' + contagem.CRIANCA;
        });

        atualizar();
    }

    /* ------------------------ 03. Pagamento ------------------------ */

    function paginaPagamento() {
        const params = new URLSearchParams(window.location.search);
        const compra = lerCompra(params);

        const incompleta = compra.some(function (p) { return !p.nome || !p.email; });
        if (compra.length === 0 || incompleta) {
            mostrarSemDados();
            return;
        }

        // Resumo
        const listaResumo = el('lista-resumo');
        compra.forEach(function (p) {
            const item = document.createElement('li');
            const nome = document.createElement('span');
            const tipo = document.createElement('span');

            nome.textContent = p.nome;
            tipo.textContent = NOMES_TIPO[p.tipo];

            item.append(nome, tipo);
            listaResumo.appendChild(item);
        });

        texto('total', moeda(totalDe(contar(compra.map(function (p) { return p.tipo; })))));

        const codigoAluno = (params.get('codigo_aluno') || '').trim();
        if (codigoAluno) {
            texto('resumo-codigo-valor', codigoAluno);
            el('resumo-codigo').hidden = false;
        }

        els('editar').forEach(function (link) {
            link.href = 'info_ingressos.html' + window.location.search;
        });

        desenharQR(el('pix-qr'), 'PIX SIMULADO - LOREM IPSUM DOLOR SIT AMET');

        // Confirmação: gera um código único por ingresso e segue para a confirmação
        const form = el('form-pagamento');
        form.addEventListener('submit', function (evento) {
            evento.preventDefault();

            const destino = new URLSearchParams(window.location.search);
            const metodo = form.querySelector('input[name="metodo"]:checked');

            destino.set('pedido', gerarCodigo('PED', 2));
            destino.set('metodo', metodo ? metodo.value : 'pix');

            compra.forEach(function (p) {
                destino.set('cod_' + p.indice, gerarCodigo('SNT', 3));
            });

            window.location.assign('confirmacao.html?' + destino.toString());
        });
    }

    /* ----------------------- 04. Confirmação ----------------------- */

    function paginaConfirmacao() {
        const params = new URLSearchParams(window.location.search);
        const compra = lerCompra(params);
        const pedido = (params.get('pedido') || '').trim();

        const invalida = compra.some(function (p) { return !p.nome || !FORMATO_CODIGO.test(p.codigo); });
        if (compra.length === 0 || invalida) {
            mostrarSemDados();
            return;
        }

        texto('pedido', pedido || '—');

        const lista = el('lista-bilhetes');
        const modelo = el('modelo-bilhete');

        compra.forEach(function (ingresso) {
            const copia = modelo.content.cloneNode(true);
            const url = urlDoIngresso(ingresso, pedido);

            preencherBilhete(copia, ingresso, pedido, url);
            el('link-ingresso', copia).href = url;

            lista.appendChild(copia);
        });

        el('imprimir').addEventListener('click', function () {
            window.print();
        });
    }

    /* --------------- Página do ingresso (destino do QR) --------------- */

    function paginaIngresso() {
        const params = new URLSearchParams(window.location.search);
        const pedido = (params.get('p') || '').trim();

        const ingresso = {
            codigo: (params.get('c') || '').trim().toUpperCase(),
            nome: (params.get('n') || '').trim(),
            email: (params.get('e') || '').trim(),
            tipo: tipoValido(params.get('t')),
            obs: (params.get('o') || '').trim()
        };

        if (!FORMATO_CODIGO.test(ingresso.codigo) || !ingresso.nome) {
            mostrarSemDados();
            return;
        }

        preencherBilhete(document, ingresso, pedido, urlDoIngresso(ingresso, pedido));
        document.title = 'Ingresso ' + ingresso.codigo + ' | Sinestesia';

        el('imprimir').addEventListener('click', function () {
            window.print();
        });
    }

    /* ---------------------------- Início ---------------------------- */

    const paginas = {
        selecao: paginaSelecao,
        participantes: paginaParticipantes,
        pagamento: paginaPagamento,
        confirmacao: paginaConfirmacao,
        ingresso: paginaIngresso
    };

    preencherPrecos();

    const iniciar = paginas[document.body.dataset.pagina];
    if (iniciar) iniciar();

})();
