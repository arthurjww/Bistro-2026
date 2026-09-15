const div = document.getElementById('divIngressos');
const forms = div.querySelectorAll('form');
const telefones = div.querySelectorAll('input[name="telefone"]');

// Aplica máscara para pessoa só digitar números
telefones.forEach(input => {
    IMask(input, {
        mask: '(00) 00000-0000'
    });
});


// Prevenir envio de forms com ENTER
forms.forEach(form => {
    form.addEventListener('submit', (event) => {
        event.preventDefault();
    });
});


/**
 * Mostra ao usuário a mensagem de erro vinda do backend (campo "erro" do JSON
 * retornado pelo Flask) e, por padrão, devolve para a tela de seleção de lugares.
*/
async function tratarErroResposta(resposta, redirecionar = true) {
    let mensagem = 'Ocorreu um erro inesperado. Tente novamente.';

    try {
        const dados = await resposta.json();
        if (dados && dados.erro) {
            mensagem = dados.erro;
        } else if (dados && dados.mensagem) {
            mensagem = dados.mensagem;
        }
    } catch (e) {
        // Corpo da resposta não veio em JSON — mantém mensagem genérica.
    }

    alert(mensagem);

    if (redirecionar) {
        window.location.href = urls.lugares;
    }
}


// Envia os dados do ingresso. Se sucesso, avança para o pagamento
async function enviarDadosESeguirPagamento() {
    for (const form of forms) {
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
    }

    const ingressos = [];

    forms.forEach(form => {
        const dados = {};

        form.querySelectorAll('input, select, textarea').forEach(input => {

            if (input.type === 'radio' && !input.checked) {
                return;
            }

            if (input.name === 'telefone') {
                dados[input.name] = input.value.replace(/\D/g, '');
            } else {
                dados[input.name] = input.value;
            }
        });

        if (dados.telefone) {
            dados.telefone = dados.telefone.replace(/\D/g, '');
        }

        ingressos.push(dados);
    });

    const payload = {
        ingressos: ingressos
    };

    try {
        const resposta = await fetch(urls.criar_ingressos, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (resposta.ok) {
            window.location.href = urls.pagamento;
            return;
        }

        await tratarErroResposta(resposta);

    } catch (erro) {
        console.error('Erro ao enviar ingressos:', erro);
        alert('Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.');
    }
}


async function cronometroAtualizado() {
    const agora = new Date();

    const diff = reservado - agora;

    if (diff <= 0) {
        document.getElementById('timer').textContent = '00:00';

        clearInterval(intervalo);
        clearInterval(verificarIntervalo);

        await verificarCronometro();

        return;
    }

    let segundos = Math.floor(diff / 1000);
    const minutos = Math.floor(segundos / 60);
    segundos = segundos % 60;

    document.getElementById('timer').textContent =
        `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
}

const intervalo = setInterval(cronometroAtualizado, 1000);
cronometroAtualizado();


let reservaExpirada = false;

async function verificarCronometro() {
    if (reservaExpirada) {
        return;
    }

    try {
        const resposta = await fetch(urls.verificar_cronometro, {
            method: 'GET'
        });

        if (reservaExpirada) {
            return;
        }

        if (resposta.status === 410) {
            reservaExpirada = true;

            const dados = await resposta.json();

            clearInterval(intervalo);
            clearInterval(verificarIntervalo);

            alert(dados.mensagem || 'O tempo da reserva expirou.');

            window.location.href = urls.lugares;

            return;
        }

        if (!resposta.ok) {
            reservaExpirada = true;
            clearInterval(intervalo);
            clearInterval(verificarIntervalo);
            await tratarErroResposta(resposta);
            return;
        }
    } catch (erro) {
        console.error('Erro ao verificar cronômetro:', erro);
    }
}

const verificarIntervalo = setInterval(verificarCronometro, 30001);