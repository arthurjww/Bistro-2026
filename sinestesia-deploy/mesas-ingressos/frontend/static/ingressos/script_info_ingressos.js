let intervalTimer = null;
let intervalVerificar = null;
let reservaExpirada = false;
let isExiting = false;
let historicoProtegido = false;

const div = document.getElementById('divIngressos');
const forms = div ? div.querySelectorAll('form') : [];
const telefones = div ? div.querySelectorAll('input[name="telefone"]') : [];

// ============================
// Proteção de Navegação (Voltar / F5)
// ============================
const eventosInteracao = ['click', 'focusin', 'keydown', 'touchstart'];

function ativarProtecaoVoltar() {
    if (historicoProtegido) return;
    historicoProtegido = true;
    history.pushState(null, null, location.href);

    // Limpa todos os escutadores de interação para liberar memória
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

// ============================
// Formatação e Eventos de Formulário
// ============================
telefones.forEach(input => {
    IMask(input, { mask: '(00) 00000-0000' });
});

forms.forEach(form => {
    form.addEventListener('submit', (event) => event.preventDefault());
});

async function tratarErroResposta(resposta, redirecionar = null) {
    let mensagem = 'Ocorreu um erro inesperado. Tente novamente.';

    if (redirecionar === null) {
        redirecionar = (resposta.status === 409 || resposta.status === 410);
    }

    if (resposta.status === 500) {
        mensagem = 'Erro interno no servidor.';
    } else {
        try {
            const dados = await resposta.json();
            mensagem = dados.erro || dados.mensagem || mensagem;
        } catch (e) {
            // Mantém mensagem padrão em respostas não-JSON
        }
    }

    alert(mensagem);

    if (redirecionar) {
        isExiting = true;
        window.location.replace(urls.lugares);
    }
}

async function enviarDadosESeguirPagamento() {
    for (const form of forms) {
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
    }

    const ingressos = Array.from(forms).map(form => {
        const dados = {};
        form.querySelectorAll('input, select, textarea').forEach(input => {
            if (!input.name || (input.type === 'radio' && !input.checked)) return;

            const valor = input.value;
            dados[input.name] = (input.name === 'telefone') ? valor.replace(/\D/g, '') : valor;
        });
        return dados;
    });

    try {
        const resposta = await fetch(urls.criar_ingressos, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingressos })
        });

        if (resposta.ok) {
            isExiting = true;
            window.location.replace(urls.pagamento);
            return;
        }

        await tratarErroResposta(resposta);

    } catch (erro) {
        console.error('Erro ao enviar ingressos:', erro);
        alert('Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.');
    }
}

// ============================
// Cronômetro da Reserva
// ============================
function pararCronometros() {
    clearInterval(intervalTimer);
    clearInterval(intervalVerificar);
}

function cronometroAtualizado() {
    const diff = reservado - new Date();

    if (diff <= 0) {
        const timerEl = document.getElementById('timer');
        if (timerEl) timerEl.textContent = '00:00';
        pararCronometros();
        verificarCronometro();
        return;
    }

    let segundos = Math.floor(diff / 1000);
    const minutos = Math.floor(segundos / 60);
    segundos = segundos % 60;

    const timerEl = document.getElementById('timer');
    if (timerEl) {
        timerEl.textContent = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
    }
}

async function verificarCronometro() {
    if (reservaExpirada) return;

    try {
        const resposta = await fetch(urls.verificar_cronometro);

        if (reservaExpirada) return;

        if (resposta.status === 410) {
            reservaExpirada = true;
            pararCronometros();

            const dados = await resposta.json();
            alert(dados.mensagem || 'O tempo da reserva expirou.');
            isExiting = true;
            window.location.replace(urls.lugares);
            return;
        }

        if (!resposta.ok) {
            reservaExpirada = true;
            pararCronometros();
            await tratarErroResposta(resposta, true);
            return;
        }
    } catch (erro) {
        console.error('Erro ao verificar cronômetro:', erro);
    }
}

// Inicialização do Cronômetro
intervalTimer = setInterval(cronometroAtualizado, 1000);
intervalVerificar = setInterval(verificarCronometro, 30001);
cronometroAtualizado();