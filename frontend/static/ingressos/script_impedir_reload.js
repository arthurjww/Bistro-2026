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