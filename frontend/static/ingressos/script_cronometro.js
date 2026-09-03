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


async function verificarCronometro() {
    try {
        const resposta = await fetch(urls.verificar_cronometro, {
            method: 'GET'
        });

        if (resposta.status === 410) {
            const dados = await resposta.json();

            clearInterval(intervalo);
            clearInterval(verificarIntervalo);

            alert(dados.mensagem);

            window.location.href = '/lugares';

            return;
        }

        if (resposta.ok) {
            const dados = await resposta.json();
            console.log('Servidor confirmou:', dados);

            if (dados.expirado) {
                window.location.href = '/lugares';
            }
        }

    } catch (erro) {
        console.error('Erro ao verificar cronômetro:', erro);
    }
}

const verificarIntervalo = setInterval(verificarCronometro, 30000);