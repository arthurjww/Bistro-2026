# Manual do Usuário - Painel Administrativo de Relatórios

Este manual orienta o uso do painel de relatórios do Bistro 2026.

O painel permite consultar participantes, pagamentos, vendas, restrições alimentares e as músicas mais votadas. Também permite gerar cada relatório em PDF.

## 1. Acesso ao painel

Para acessar o painel:

1. Abra um navegador de internet, como Google Chrome, Microsoft Edge ou Firefox.
2. Acesse o endereço do painel administrativo fornecido pela equipe técnica.
3. Digite o e-mail e a senha cadastrados para o administrador.
4. Selecione **Entrar**.

Se os dados estiverem incorretos, o sistema exibirá uma mensagem de erro. Confira o e-mail e a senha e tente novamente.

O painel é protegido. Se uma pessoa tentar acessar diretamente o endereço dos relatórios sem estar conectada, será encaminhada para a página de login.

> Não compartilhe sua senha. Ao terminar, use o botão **Sair**, principalmente em computadores compartilhados.

## 2. Organização do painel

Na parte superior da página estão disponíveis as seguintes seções:

- **Resumo de Participantes**
- **Visão Geral**
- **Financeiro**
- **Vendas**
- **Restrições Alimentares**
- **Top 5 Músicas**

Selecione o nome de uma seção para abrir o relatório correspondente.

## 3. Filtro por dia do Bistro

O campo **Dia do Bistro** permite consultar um dia específico do evento.

Para usar o filtro:

1. Selecione a data desejada.
2. Selecione **Aplicar filtro**.
3. Confira se a data escolhida permanece selecionada.

A opção **Todos os dias** reúne os registros dos dois dias do evento.

O filtro de dia afeta:

- Resumo de Participantes;
- Visão Geral;
- Financeiro;
- Vendas;
- Restrições Alimentares.

O filtro não altera o **Top 5 Músicas** nem o número **Ingressos Restantes - Geral**.

## 4. Resumo de Participantes

O Resumo de Participantes apresenta, em uma única tabela, todos os participantes confirmados para o dia selecionado.

A tabela contém:

- **Técnico:** curso do aluno responsável;
- **Aluno Responsável:** aluno cujo código foi usado na compra;
- **Participante:** pessoa que utilizará o ingresso;
- **Valor Pago:** valor confirmado para o ingresso;
- **Data da Compra:** data e horário em que o ingresso foi registrado;
- **Dia do Bistro:** dia em que o participante irá ao evento;
- **Restrição:** informa se existe restrição alimentar;
- **Mesa / Lugar:** posição reservada para o participante.

Este relatório considera apenas ingressos com pagamento confirmado. Ele foi organizado como uma tabela única para facilitar a consulta e a impressão da lista completa.

## 5. Visão Geral

A Visão Geral é usada para localizar um participante específico e consultar suas informações completas.

### Como consultar

1. Se necessário, escolha um dia no filtro **Dia do Bistro** e selecione **Aplicar filtro**.
2. Abra a seção **Visão Geral**.
3. Selecione o curso no campo **Técnico**.
4. Selecione o **Aluno Responsável**.
5. Selecione o **Participante**.

Os campos são atualizados automaticamente depois de cada escolha. Não é necessário selecionar outro botão para aplicar os filtros da Visão Geral.

Depois da seleção, serão exibidos:

- aluno responsável;
- nome do participante;
- número do ingresso;
- telefone do participante;
- restrições alimentares;
- data e hora da compra;
- dia do Bistro;
- situação do pagamento.

Se um aluno aparecer no filtro, mas não apresentar participantes, verifique o dia selecionado. O aluno pode não possuir ingressos vinculados naquela data.

### Situação do pagamento

- **Pago:** pagamento confirmado.
- **Não pago:** ingresso criado, mas ainda pendente de confirmação.

Ingressos não pagos podem aparecer temporariamente enquanto o pagamento estiver pendente.

## 6. Relatório Financeiro

O relatório Financeiro considera somente ingressos com pagamento confirmado.

Os indicadores apresentados são:

- **Faturamento Total:** soma dos valores dos ingressos confirmados;
- **Total de Ingressos Confirmados:** quantidade total de ingressos confirmados, incluindo ingressos gratuitos;
- **Valor Médio por Ingresso Confirmado:** média dos valores dos ingressos confirmados.

Ingressos gratuitos possuem valor de `R$ 0,00`, mas entram na quantidade total de ingressos confirmados e no cálculo do valor médio.

### Informações por aluno

Cada aluno aparece uma vez, acompanhado da **Quantidade de Ingressos Confirmados**.

Para consultar os ingressos daquele aluno:

1. Localize o aluno.
2. Selecione **Exibir detalhes**.
3. Para fechar a lista, selecione **Ocultar detalhes**.

Os detalhes apresentam:

- número do ingresso;
- nome do participante;
- telefone;
- data e horário da compra;
- dia do Bistro;
- valor pago.

## 7. Relatório de Vendas

O relatório de Vendas é usado para acompanhar os ingressos registrados, inclusive aqueles que ainda não tiveram o pagamento confirmado.

Os indicadores são:

- **Ingressos Pagos:** quantidade com pagamento confirmado;
- **Ingressos Não Pagos:** quantidade pendente de pagamento;
- **Ingressos Restantes - Geral:** soma dos ingressos que ainda podem ser utilizados pelos alunos.

O número de ingressos restantes é geral e não muda quando um dia específico é selecionado.

### Informações por aluno

Cada aluno apresenta:

- **Quantidade de Ingressos Vinculados:** ingressos associados ao aluno no dia selecionado;
- **Quantidade de Ingressos Restantes:** ingressos que o aluno ainda pode utilizar.

Selecione **Exibir detalhes** para consultar:

- número do ingresso;
- lugar e salão;
- dia do Bistro;
- situação do pagamento.

### Diferença entre Vendas e Financeiro

- **Vendas:** acompanha ingressos pagos, não pagos, vinculados e restantes.
- **Financeiro:** considera somente ingressos confirmados e apresenta os valores recebidos.

Por esse motivo, um ingresso pendente pode aparecer em Vendas e não aparecer no Financeiro.

## 8. Restrições Alimentares

Este relatório reúne participantes confirmados que possuem alguma restrição alimentar registrada.

A tabela apresenta:

- participante;
- número do ingresso;
- mesa e lugar;
- dia do Bistro;
- restrição informada.

Participantes sem restrição não aparecem nessa lista. Ingressos sem pagamento confirmado também não são incluídos.

Este relatório deve ser conferido pela equipe responsável pela preparação e pelo atendimento das refeições.

## 9. Top 5 Músicas

O Top 5 Músicas apresenta as cinco músicas mais votadas.

A tabela contém:

- posição ou número da música;
- nome da música;
- artista;
- quantidade de votos.

O filtro por dia do Bistro não altera esse relatório.

## 10. Geração de PDF

Cada seção possui o botão **Gerar PDF**.

Para salvar um relatório:

1. Abra a seção desejada.
2. Aplique o filtro de dia, se necessário.
3. Confira os dados exibidos.
4. Selecione **Gerar PDF**.
5. Na janela de impressão do navegador, escolha **Salvar como PDF**.
6. Confira a visualização das páginas.
7. Escolha a pasta e o nome do arquivo.
8. Selecione **Salvar**.

Os detalhes dos alunos são incluídos no PDF de Financeiro e Vendas mesmo quando estiverem fechados na tela.

O relatório pode utilizar mais de uma página. Isso evita reduzir demais o conteúdo ou cortar informações.

## 11. Encerramento da sessão

Ao terminar:

1. Localize a identificação do administrador na parte superior do painel.
2. Selecione **Sair**.
3. Confirme que a página de login voltou a aparecer.

Não feche apenas a aba quando estiver usando um computador compartilhado. Utilize sempre o botão **Sair**.

## 12. Solução de problemas

### Nenhum dado foi encontrado

- Confira o dia selecionado.
- Escolha **Todos os dias** para verificar se existem registros em outra data.
- Na Visão Geral, confira se o curso, o aluno e o participante foram selecionados na ordem correta.
- Um ingresso pendente pode ainda não aparecer nos relatórios que exigem pagamento confirmado.

### Um aluno aparece sem participantes

O aluno pode não possuir participantes no dia selecionado. Escolha outro dia ou **Todos os dias**.

### O pagamento ainda aparece como pendente

A confirmação pode levar alguns instantes. Atualize a página depois de aguardar. Se o problema continuar, informe o número do ingresso à equipe técnica.

### A página parece desatualizada

Atualize normalmente o navegador. Se necessário, use `Ctrl + F5` para recarregar todos os arquivos da página.

### O PDF não ficou correto

- Confira a pré-visualização antes de salvar.
- Utilize papel A4.
- Mantenha a orientação definida automaticamente pelo relatório.
- Evite alterar manualmente a escala, exceto se a pré-visualização indicar necessidade.

### Não foi possível entrar

- Confira se o e-mail foi digitado corretamente.
- Verifique letras maiúsculas, minúsculas e caracteres especiais da senha.
- Solicite à equipe técnica a confirmação do cadastro. Por segurança, não envie sua senha por mensagens.

## 13. Boas práticas

- Confira o dia selecionado antes de analisar ou imprimir um relatório.
- Gere um novo PDF quando os dados forem atualizados.
- Não altere informações diretamente no banco de dados.
- Não compartilhe credenciais administrativas.
- Saia do sistema ao terminar.
- Em caso de divergência, anote o número do ingresso e informe a equipe técnica.
