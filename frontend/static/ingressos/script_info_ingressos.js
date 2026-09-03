const inputCodigo = document.getElementById('input_codigo');
const details = document.getElementById('detailIngressos');
const forms = details.querySelectorAll('form');

const reservado = new Date(
    {{ cronometro.isoformat() | tojson }}
);


forms.forEach(form => {
    form.addEventListener('submit', (event) => {
        event.preventDefault();
    });
});


details.addEventListener('click', (event) => {
    if (details.dataset.podeAbrir === 'false') {
        event.preventDefault();
    }
});


function cronometroAtualizado() {
    const agora = new Date();

    const diff = 15 * 60 * 1000 - (agora - reservado);

    if (diff <= 0) {
        document.getElementById('timer').textContent = '00:00';
        clearInterval(intervalo);
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


async function confirmarCodigoAluno() {
    const params = new URLSearchParams({
        codigo: inputCodigo.value
    });

    const resposta = await fetch(`${urls.confirmar_codigo}?${params}`, {
        method: 'GET',
    });

    if (resposta.ok) {
        const dados = await resposta.json();
        inputCodigo.parentElement.querySelector('span').textContent =
            `${dados.sucesso}\nApós usar esses ingressos, sobrará ${dados.usos_restantes} usos do código`;
        details.dataset.podeAbrir = 'true';
        // dá para colocar mudanças do css aqui
    } else if (resposta.status === 409) {
        window.location.href = '/lugares';
        return;
    }
}


async function enviarDadosESeguirPagamento() {
    if (details.dataset.podeAbrir === 'false') {
        alert('Você não usou um código confirmado');
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
            dados[input.name] = input.value;
        });

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