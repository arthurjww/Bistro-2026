const reservado = new Date(
    {{ cronometro.isoformat() | tojson }}
);

function cronometroAtualizado() {
    const agora = new Date();

    const diff = agora - reservado;

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

cronometroAtualizado();

const intervalo = setInterval(cronometroAtualizado, 1000);