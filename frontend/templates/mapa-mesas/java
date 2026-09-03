
const API_BASE = "/api";

async function carregarMapa() {
    const resposta = await fetch(`${API_BASE}/mapa`);
    const mapa = await resposta.json();
    renderizarMapa(mapa);
}

function renderizarMapa(mapa) {
    const container = document.getElementById("mapa");
    container.innerHTML = "";

    mapa.forEach(lugar => {
        const botao = document.createElement("button");
        botao.textContent = `${lugar.cod_lugar} (${lugar.status})`;
        botao.className = `lugar status-${lugar.status}`;
        botao.addEventListener("click", () => clicarLugar(lugar));
        container.appendChild(botao);
    });
}

function clicarLugar(lugar) {
    if (lugar.status === "livre") {
        escolherLugar(lugar.cod_lugar);
    } else if (lugar.status === "em_pagamento") {
        confirmarPagamento(lugar.cod_lugar);
    } else if (lugar.status === "ocupado") {
        cancelarReserva(lugar.cod_lugar);
    }
}

async function escolherLugar(codLugar) {
    const resposta = await fetch(`${API_BASE}/lugares/${codLugar}/escolher`, {
        method: "POST"
    });
    const dados = await resposta.json();

    if (!resposta.ok) {
        alert(dados.erro || "Erro ao escolher lugar.");
        return;
    }

    carregarMapa();
}

async function confirmarPagamento(codLugar) {
    const resposta = await fetch(`${API_BASE}/lugares/${codLugar}/confirmar`, {
        method: "POST"
    });
    const dados = await resposta.json();

    if (!resposta.ok) {
        alert(dados.erro || "Erro ao confirmar pagamento.");
        return;
    }

    carregarMapa();
}

async function cancelarReserva(codLugar) {
    const resposta = await fetch(`${API_BASE}/lugares/${codLugar}/cancelar`, {
        method: "POST"
    });
    const dados = await resposta.json();

    if (!resposta.ok) {
        alert(dados.erro || "Erro ao cancelar reserva.");
        return;
    }

    carregarMapa();
}

document.addEventListener("DOMContentLoaded", carregarMapa);