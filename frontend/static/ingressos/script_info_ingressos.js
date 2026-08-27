const inputCodigo = document.getElementById('input_codigo');
const details = document.getElementById('detailIngressos');

const reservado = new Date(
    {{ cronometro.isoformat() | tojson }}
);


cronometroAtualizado();


details.addEventListener('click', function (event) {
    if (details.dataset.podeAbrir === 'false') {
        event.preventDefault();
    }
})


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



async function confirmarCodigoAluno() {
    const payload = {
        codigo: inputCodigo.value
    };

    const resposta = await fetch('/info_ingressos/confirmar_codigo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    if (resposta.ok) {
        const dados = await resposta.json();
        inputCodigo.parentElement.querySelector('span').textContent =
            `${dados.sucesso}\nApós usar esses ingressos, sobrará ${dados.usos_restantes} usos do código`;
        details.dataset.podeAbrir = 'true';
        // dá para colocar mudanças do css aqui
    }
}


async function enviarDadosESeguirPagamento() {
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
}