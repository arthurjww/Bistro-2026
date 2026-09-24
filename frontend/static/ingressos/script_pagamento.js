let intervalPolling = null;
let intervalTimer = null;
let intervalVerificar = null;
let reservaExpirada = false;
let pagamentoConfirmado = false;
let isExiting = false;
let historicoProtegido = false;

// ============================
// Proteção de Navegação (Voltar / F5)
// ============================
const eventosInteracao = ['click', 'focusin', 'keydown', 'touchstart'];

function ativarProtecaoVoltar() {
    if (historicoProtegido) return;
    historicoProtegido = true;
    history.pushState(null, null, location.href);

    eventosInteracao.forEach(evento => {
        window.removeEventListener(evento, ativarProtecaoVoltar);
    });
}

eventosInteracao.forEach(evento => {
    window.addEventListener(evento, ativarProtecaoVoltar);
});

// Intercepta a seta "Voltar" -> Redireciona para /lugares
window.addEventListener('popstate', function () {
    if (isExiting || !historicoProtegido) return;

    if (confirm("Você tem certeza? Você perderá todo o seu progresso e retornará à seleção de lugares.")) {
        isExiting = true;
        window.location.replace(urls.lugares);
    } else {
        history.pushState(null, null, location.href);
    }
});

// Intercepta F5 / Recarregar / Fechar Aba
window.addEventListener('beforeunload', function (e) {
    if (isExiting) return;
    e.preventDefault();
    e.returnValue = '';
});

// Navegação por histórico (Back/Forward) força retorno para /lugares
window.addEventListener('pageshow', function (event) {
    const navEntries = performance.getEntriesByType?.('navigation');
    const isBackForward = navEntries && navEntries[0]?.type === 'back_forward';

    if (event.persisted || isBackForward) {
        isExiting = true;
        window.location.replace(urls.lugares);
    }
});

function pararTodosIntervalos() {
    clearInterval(intervalPolling);
    clearInterval(intervalTimer);
    clearInterval(intervalVerificar);
}

// ============================
// Máscara e Submissão do Formulário
// ============================
const inputCpf = document.getElementById('cpf');
if (inputCpf) {
    IMask(inputCpf, { mask: '000.000.000-00' });
}

const formPagamento = document.getElementById('form-pagamento');
if (formPagamento) {
    formPagamento.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (reservaExpirada) return;

        const btn = document.getElementById('btn-submit');
        const erroDiv = document.getElementById('alerta-erro');

        btn.disabled = true;
        btn.innerText = "Gerando PIX...";
        if (erroDiv) erroDiv.style.display = 'none';

        const payload = {
            payer: {
                email: document.getElementById('email')?.value.trim() || null,
                first_name: document.getElementById('nome')?.value.trim() || '',
                identification: {
                    type: "CPF",
                    number: inputCpf ? inputCpf.value.replace(/\D/g, '') : null
                }
            }
        };

        try {
            const response = await fetch(urls.pagamento, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.sucesso) {

                // Ingressos gratuitos/isentos confirmados direto
                if (data.status === 'processed') {
                    pagamentoConfirmado = true;
                    isExiting = true;
                    pararTodosIntervalos();
                    window.location.replace(urls.pagamento_sucesso);
                    return;
                }

                // Exibe o QR Code e chave PIX
                document.getElementById('qr-code-img').src = `data:image/png;base64,${data.pix.qr_code_base64}`;
                document.getElementById('qr-code-text').value = data.pix.qr_code;

                if (data.pix.ticket_url) {
                    const linkTicket = document.getElementById('ticket-url');
                    if (linkTicket) linkTicket.href = data.pix.ticket_url;

                    const ticketContainer = document.getElementById('ticket-link-container');
                    if (ticketContainer) ticketContainer.style.display = 'block';
                }

                formPagamento.style.display = 'none';
                document.getElementById('area-pix').style.display = 'block';

                iniciarPollingStatus();

            } else {
                mostrarErro(data.erro || 'Falha ao gerar o pagamento.');
                btn.disabled = false;
                btn.innerText = "Gerar QR Code PIX";
            }

        } catch (err) {
            console.error(err);
            mostrarErro('Erro de conexão com o servidor. Tente novamente.');
            btn.disabled = false;
            btn.innerText = "Gerar QR Code PIX";
        }
    });
}

// Botão Copiar PIX
const btnCopiar = document.getElementById('btn-copiar');
if (btnCopiar) {
    btnCopiar.addEventListener('click', function () {
        const inputChave = document.getElementById('qr-code-text');
        if (!inputChave) return;

        inputChave.select();
        navigator.clipboard.writeText(inputChave.value);

        const originalText = this.innerText;
        this.innerText = "Copiado!";
        this.style.backgroundColor = "#2b8a3e";

        setTimeout(() => {
            this.innerText = originalText;
            this.style.backgroundColor = "#4db8ff";
        }, 2000);
    });
}

// ============================
// Polling de Status do Pagamento
// ============================
function iniciarPollingStatus() {
    if (intervalPolling) return;

    intervalPolling = setInterval(async () => {
        try {
            const response = await fetch(urls.pagamento_status);
            const data = await response.json();

            if (data.pago) {
                pagamentoConfirmado = true;
                isExiting = true;
                pararTodosIntervalos();

                const spinner = document.getElementById('spinner');
                if (spinner) spinner.style.display = 'none';

                const statusTexto = document.getElementById('texto-status');
                if (statusTexto) {
                    statusTexto.innerText = "Pagamento Aprovado! Redirecionando...";
                    statusTexto.parentElement.style.backgroundColor = "#d3f9d8";
                    statusTexto.parentElement.style.color = "#2b8a3e";
                }

                setTimeout(() => {
                    window.location.replace(urls.pagamento_sucesso);
                }, 1500);
                return;
            }

            if (data.falhou) {
                clearInterval(intervalPolling);
                intervalPolling = null;

                document.getElementById('area-pix').style.display = 'none';
                if (formPagamento) formPagamento.style.display = 'block';

                const btn = document.getElementById('btn-submit');
                if (btn) {
                    btn.disabled = false;
                    btn.innerText = "Gerar QR Code PIX";
                }

                mostrarErro('O pagamento não foi aprovado (status: ' + data.status + '). Tente novamente.');
            }
        } catch (err) {
            console.error("Erro na verificação de status:", err);
        }
    }, 3000);
}

function mostrarErro(mensagem) {
    const erroDiv = document.getElementById('alerta-erro');
    if (erroDiv) {
        erroDiv.innerText = mensagem;
        erroDiv.style.display = 'block';
    }
}

// ============================
// Cronômetro
// ============================
function cronometroAtualizado() {
    const diff = reservado - new Date();
    const timerEl = document.getElementById('timer');
    if (!timerEl) return;

    if (diff <= 0) {
        timerEl.textContent = '00:00';
        pararTodosIntervalos();
        verificarCronometro();
        return;
    }

    let segundos = Math.floor(diff / 1000);
    const minutos = Math.floor(segundos / 60);
    segundos = segundos % 60;

    timerEl.textContent = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
}

async function verificarCronometro() {
    if (reservaExpirada || pagamentoConfirmado) return;

    try {
        const resposta = await fetch(urls.verificar_cronometro);

        if (reservaExpirada || pagamentoConfirmado) return;

        if (resposta.status === 410) {
            reservaExpirada = true;
            isExiting = true;
            pararTodosIntervalos();

            const dados = await resposta.json();
            alert(dados.mensagem || 'O tempo da reserva expirou.');
            window.location.replace(urls.lugares);
            return;
        }

        if (!resposta.ok) {
            reservaExpirada = true;
            isExiting = true;
            pararTodosIntervalos();

            let mensagem = 'Ocorreu um erro inesperado. Tente novamente.';
            try {
                const dados = await resposta.json();
                mensagem = dados.erro || dados.mensagem || mensagem;
            } catch (e) {
                // Mantém mensagem padrão
            }

            alert(mensagem);
            window.location.replace(urls.lugares);
            return;
        }

    } catch (erro) {
        console.error('Erro ao verificar cronômetro:', erro);
    }
}

// Inicialização dos cronômetros
intervalTimer = setInterval(cronometroAtualizado, 1000);
intervalVerificar = setInterval(verificarCronometro, 30001);
cronometroAtualizado();