const expira = new Date(
    {{ cronometro.isoformat() | tojson }}
);


function cronometroAtualizado() {
    const agora = new Date();

    const diff = agora - expira;

    if (diff <= 0) {
        return void;
    }

    let segundos = Math.floor(diff / 1000);
    const minutos = Math.floor(segundos / 60);
    segundos = segundos % 60;

    document.getElementById('timer').textContent =
        `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`
}


function