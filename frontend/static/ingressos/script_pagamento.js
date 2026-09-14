// ============================
// Estado dos 3 intervalos (evita conflito entre eles)
// ============================
let intervalPolling = null;   // consulta o status do pagamento PIX (a cada 3s)
let intervalTimer = null;     // atualiza o contador visual do cronômetro (a cada 1s)
let intervalVerificar = null; // confirma no servidor se a reserva expirou (a cada 30s)
let reservaExpirada = false;
let pagamentoConfirmado = false;

function pararTodosIntervalos() {
  clearInterval(intervalPolling);
  clearInterval(intervalTimer);
  clearInterval(intervalVerificar);
}

// ============================
// Formatação simples de CPF
// ============================
document.getElementById('cpf').addEventListener('input', function (e) {
  let v = e.target.value.replace(/\D/g, '');
  if (v.length > 11) v = v.slice(0, 11);
  e.target.value = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
});

// ============================
// Envio do Formulário para a rota POST /pagamento (urls.pagamento)
// ============================
document.getElementById('form-pagamento').addEventListener('submit', async function (e) {
  e.preventDefault();

  if (reservaExpirada) return;

  const btn = document.getElementById('btn-submit');
  const erroDiv = document.getElementById('alerta-erro');

  btn.disabled = true;
  btn.innerText = "Gerando PIX...";
  erroDiv.style.display = 'none';

  // Payload conforme processar_pagamento() espera (payer.email / first_name / identification)
  const payload = {
    payer: {
      email: document.getElementById('email').value.trim() || null,
      first_name: document.getElementById('nome').value.trim(),
      identification: {
        type: "CPF",
        number: document.getElementById('cpf').value.replace(/\D/g, '') || null
      }
    }
  };

  try {
    const response = await fetch(urls.pagamento, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok && data.sucesso) {

      // Caso o pagamento já tenha sido confirmado direto (ex: R$ 0,00 / grátis)
      if (data.status === 'processed') {
        pagamentoConfirmado = true;
        pararTodosIntervalos();
        window.location.href = urls.pagamento_sucesso;
        return;
      }

      // Preenche a imagem do QR Code em Base64
      document.getElementById('qr-code-img').src = `data:image/png;base64,${data.pix.qr_code_base64}`;

      // Preenche a chave Copia e Cola
      document.getElementById('qr-code-text').value = data.pix.qr_code;

      // Link do ticket, caso exista
      if (data.pix.ticket_url) {
        const linkTicket = document.getElementById('ticket-url');
        linkTicket.href = data.pix.ticket_url;
        document.getElementById('ticket-link-container').style.display = 'block';
      }

      // Alterna visibilidade da tela
      document.getElementById('form-pagamento').style.display = 'none';
      document.getElementById('area-pix').style.display = 'block';

      // Inicia o polling para checar se o pagamento foi confirmado
      iniciarPollingStatus();

    } else {
      mostrarErro(data.erro || 'Falha ao gerar o pagamento.');
      btn.disabled = false;
      btn.innerText = "Gerar QR Code PIX";
    }

  } catch (err) {
    console.error(err);
    mostrarErro('Erro de conexão com o servidor. Tente novamente.');
    btn.disabled = false;
    btn.innerText = "Gerar QR Code PIX";
  }
});

// ============================
// Botão de Copiar Chave PIX
// ============================
document.getElementById('btn-copiar').addEventListener('click', function () {
  const inputChave = document.getElementById('qr-code-text');
  inputChave.select();
  navigator.clipboard.writeText(inputChave.value);

  const originalText = this.innerText;
  this.innerText = "Copiado!";
  this.style.backgroundColor = "#2b8a3e";

  setTimeout(() => {
    this.innerText = originalText;
    this.style.backgroundColor = "#4db8ff";
  }, 2000);
});

// ============================
// Consulta urls.pagamento_status a cada 3 segundos
// ============================
function iniciarPollingStatus() {
  if (intervalPolling) return; // evita duplicar o polling se o form for reenviado

  intervalPolling = setInterval(async () => {
    try {
      const response = await fetch(urls.pagamento_status);
      const data = await response.json();

      if (data.pago) {
        pagamentoConfirmado = true;
        pararTodosIntervalos();

        document.getElementById('spinner').style.display = 'none';
        const statusTexto = document.getElementById('texto-status');
        statusTexto.innerText = "Pagamento Aprovado! Redirecionando...";
        statusTexto.parentElement.style.backgroundColor = "#d3f9d8";
        statusTexto.parentElement.style.color = "#2b8a3e";

        setTimeout(() => {
          window.location.href = urls.pagamento_sucesso;
        }, 1500);
        return;
      }

    if (typeof data.cronometro === 'number') {
        reservado = data.cronometro;
        cronometroAtualizado();
      }

      // Pix rejeitado/expirado/cancelado no Mercado Pago: para de esperar
      // e deixa o usuário tentar gerar um novo Pix.
      if (data.falhou) {
        clearInterval(intervalPolling);
        intervalPolling = null;

        document.getElementById('area-pix').style.display = 'none';
        document.getElementById('form-pagamento').style.display = 'block';

        const btn = document.getElementById('btn-submit');
        btn.disabled = false;
        btn.innerText = "Gerar QR Code PIX";

        mostrarErro('O pagamento não foi aprovado (status: ' + data.status + '). Tente novamente.');
      }
    } catch (err) {
      console.error("Erro na verificação de status:", err);
    }
  }, 3000);
}

function mostrarErro(mensagem) {
  const erroDiv = document.getElementById('alerta-erro');
  erroDiv.innerText = mensagem;
  erroDiv.style.display = 'block';
}

function cronometroAtualizado() {
  const agora = new Date();
  const diff = reservado - agora;

  const timerEl = document.getElementById('timer');
  if (!timerEl) return;

  if (diff <= 0) {
    timerEl.textContent = '00:00';

    clearInterval(intervalTimer);
    clearInterval(intervalVerificar);

    verificarCronometro();
    return;
  }

  let segundos = Math.floor(diff / 1000);
  const minutos = Math.floor(segundos / 60);
  segundos = segundos % 60;

  timerEl.textContent =
    `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
}

async function verificarCronometro() {
  if (reservaExpirada || pagamentoConfirmado) return;

  try {
    const resposta = await fetch(urls.verificar_cronometro);

    if (reservaExpirada || pagamentoConfirmado) return;

    if (resposta.status === 410) {
      reservaExpirada = true;
      const dados = await resposta.json();

      pararTodosIntervalos();
      alert(dados.mensagem || 'O tempo da reserva expirou.');
      window.location.href = urls.lugares;
      return;
    }

    if (!resposta.ok) {
      reservaExpirada = true;
      pararTodosIntervalos();

      let mensagem = 'Ocorreu um erro inesperado. Tente novamente.';
      try {
        const dados = await resposta.json();
        if (dados && dados.erro) {
          mensagem = dados.erro;
        } else if (dados && dados.mensagem) {
          mensagem = dados.mensagem;
        }
      } catch (e) {
        // corpo da resposta não veio em JSON — mantém mensagem genérica
      }

      alert(mensagem);
      window.location.href = urls.lugares;
      return;
    }

  } catch (erro) {
    console.error('Erro ao verificar cronômetro:', erro);
  }
}

// Inicializa o cronômetro assim que a tela de pagamento carrega
intervalTimer = setInterval(cronometroAtualizado, 1000);
cronometroAtualizado();
intervalVerificar = setInterval(verificarCronometro, 30001);