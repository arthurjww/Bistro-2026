const inputCodigo = document.getElementById('input_codigo');
const details = document.getElementById('detailIngressos');
const forms = details.querySelectorAll('form');
const telefones = document.querySelectorAll('#telefone');


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


// Prevenir abertura do details sem ter posto o código do aluno
details.addEventListener('click', (event) => {
    if (details.dataset.podeAbrir === 'false') {
        event.preventDefault();
    }
});


// Manda fetch para confirmar código do aluno. Se confirmado, permite details ser aberto
async function confirmarCodigoAluno() {
    const params = new URLSearchParams({
        codigo: inputCodigo.value
    });

    const resposta = await fetch(`${urls.confirmar_codigo}?${params}`, {
        method: 'GET',
    });

    if (resposta.ok) {
        const dados = await resposta.json();
        if (dados.sucesso === 'Código confirmado.') {
            inputCodigo.parentElement.querySelector('span').textContent =
                `${dados.sucesso}\nApós usar esses ingressos, sobrará ${dados.usos_restantes} usos do código`;
            details.dataset.podeAbrir = 'true';
        }
        // dá para colocar mudanças do css aqui
    } else {
        const dados = await resposta.json()
        if (dados.erro === 'A reserva expirou.') {
            window.location.href = '/lugares';
            return;
        } else {
            inputCodigo.parentElement.querySelector('span').textContent = dados.erro;
        }

    }
}

// Envia os dados do ingresso. Se sucesso, avança para o pagamento
async function enviarDadosESeguirPagamento() {
    if (details.dataset.podeAbrir === 'false') {
        alert('Você não usou um código confirmado');
        return;
    }
    for (const form of forms) {
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
    }

    const ingressos = [];

    details.querySelectorAll('form').forEach(form => {
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

            dados[input.name] = input.value;
        });

        if (dados.telefone) {
            dados.telefone = dados.telefone.replace(/\D/g, '');
        }

        ingressos.push(dados);
    });

    const payload = {
        ingressos: ingressos
    };

    const resposta = await fetch(urls.criar_ingressos, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (resposta.ok) {
        window.location.href = '/pagamento';
        return;
    }
}