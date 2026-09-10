const inputCodigo = document.getElementById('input_codigo');
const div = document.getElementById('divIngressos');
const forms = div.querySelectorAll('form');


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
            // se vira Davi
        }
        // dá para colocar mudanças do css aqui
    } else {
        const dados = await resposta.json()
        inputCodigo.parentElement.querySelector('span').textContent = dados.erro;
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