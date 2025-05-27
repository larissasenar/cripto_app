const hamburger = document.querySelector(".hamburger");
const sidebar = document.querySelector(".sidebar");

hamburger.addEventListener("click", () => {
  sidebar.classList.toggle("active");
});

// =============================================================================
// Variáveis Globais (populadas via Jinja2 no HTML antes deste script)
// =============================================================================

// dadosDoGraficoParaExportacao: Usado para exportar os dados brutos do gráfico (CSV).
// Deve ser um array de objetos, por exemplo: [{ data: "2024-05-20", valor: 100000 }, ...]
// Populado no HTML assim: var dadosDoGraficoParaExportacao = {{ dados | tojson }};
let dadosDoGraficoParaExportacao = [];

// labels: Usado para os rótulos do eixo X do gráfico (datas/períodos).
// Populado no HTML assim: var labels = {{ labels | tojson }};
let labels = [];

// dados: Usado para os valores do eixo Y do gráfico (preços).
// Populado no HTML assim: var dados = {{ dados | tojson }};
let dados = [];

// =============================================================================
// Funções de Exportação
// =============================================================================

/**
 * Alterna a visibilidade do dropdown de exportação.
 */
function toggleExportDropdown() {
  document.getElementById("exportDropdownContent").classList.toggle("show");
}

/**
 * Exporta o gráfico do canvas como uma imagem (JPEG).
 * @param {string} format O formato da imagem a ser exportada (apenas 'jpeg' é suportado aqui).
 */
function exportChart(format = "jpeg") {
  const canvas = document.getElementById("grafico-canvas");
  if (!canvas) {
    console.error(
      "Canvas 'grafico-canvas' não encontrado. Certifique-se de que o ID está correto e o canvas existe."
    );
    return;
  }

  const link = document.createElement("a");
  const criptoSelect = document.getElementById("cripto");
  // Tenta obter o nome da criptomoeda selecionada, caso contrário, usa 'cripto'
  const moeda =
    criptoSelect && criptoSelect.options[criptoSelect.selectedIndex]
      ? criptoSelect.options[criptoSelect.selectedIndex].text
      : "cripto";

  if (format === "jpeg") {
    link.download = `grafico-${moeda.toLowerCase()}.jpeg`;
    // Qualidade de 0.9 para JPEG (pode ser ajustada de 0 a 1).
    // JPEG é um formato com perdas, o que significa que pode haver alguma degradação de qualidade.
    link.href = canvas.toDataURL("image/jpeg", 0.9);
  } else {
    // Fallback: se um formato não suportado for passado, ainda tenta exportar como JPEG.
    console.warn(
      `Formato de imagem "${format}" não suportado para exportChart. Exportando como JPEG.`
    );
    link.download = `grafico-${moeda.toLowerCase()}.jpeg`;
    link.href = canvas.toDataURL("image/jpeg", 0.9);
  }
  link.click();
  // Fecha o dropdown após a exportação
  document.getElementById("exportDropdownContent").classList.remove("show");
}

/**
 * Exporta os dados subjacentes do gráfico como CSV.
 * @param {string} type O tipo de arquivo para exportar os dados (apenas 'csv' é suportado aqui).
 */
function exportChartData(type) {
  // Verifica se 'dadosDoGraficoParaExportacao' foi populado
  const data =
    typeof dadosDoGraficoParaExportacao !== "undefined"
      ? dadosDoGraficoParaExportacao
      : [];

  if (data.length === 0) {
    console.warn(
      "Nenhum dado disponível para exportação. Verifique se 'dadosDoGraficoParaExportacao' está populado."
    );
    // Você pode adicionar uma mensagem visual para o usuário aqui (ex: um modal customizado).
    return;
  }

  const criptoSelect = document.getElementById("cripto");
  const moeda =
    criptoSelect && criptoSelect.options[criptoSelect.selectedIndex]
      ? criptoSelect.options[criptoSelect.selectedIndex].text
      : "cripto";
  const filename = `dados_grafico_${moeda.toLowerCase()}.${type}`;

  if (type === "csv") {
    let csvContent = "data:text/csv;charset=utf-8,";
    // Adiciona cabeçalhos CSV. Adapte estes cabeçalhos para as chaves reais dos seus objetos de dados.
    // Por exemplo, se seus dados são { data: "...", valor: "..." }, os cabeçalhos seriam "Data,Valor".
    csvContent += "Data,Valor\n";

    data.forEach((item) => {
      // Adapte 'item.data' e 'item.valor' para as propriedades reais dos seus objetos de dados.
      // Certifique-se de que 'item.data' está formatado para ser legível (ex: 'YYYY-MM-DD').
      const row = `${item.data},${item.valor}`;
      csvContent += row + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link); // Necessário para compatibilidade com Firefox
    link.click();
    document.body.removeChild(link);
  } else {
    console.error("Formato de exportação de dados não suportado:", type);
  }
  // Fecha o dropdown após a exportação
  document.getElementById("exportDropdownContent").classList.remove("show");
}

// =============================================================================
// Lógica Principal (executada quando o DOM está pronto)
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Lógica do Hamburger e Sidebar
  const hamburger = document.querySelector(".hamburger");
  const sidebar = document.getElementById("sidebar");
  const body = document.body;

  if (hamburger && sidebar) {
    hamburger.addEventListener("click", () => {
      const expanded = hamburger.getAttribute("aria-expanded") === "true";
      hamburger.setAttribute("aria-expanded", !expanded);
      sidebar.classList.toggle("active");
      body.classList.toggle("sidebar-open");
    });

    sidebar.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
          sidebar.classList.remove("active");
          hamburger.setAttribute("aria-expanded", false);
          body.classList.remove("sidebar-open");
        }
      });
    });

    body.addEventListener("click", (event) => {
      if (
        body.classList.contains("sidebar-open") &&
        !sidebar.contains(event.target) &&
        !hamburger.contains(event.target)
      ) {
        sidebar.classList.remove("active");
        hamburger.setAttribute("aria-expanded", false);
        body.classList.remove("sidebar-open");
      }
    });
  } else {
    console.warn(
      "Elementos .hamburger ou #sidebar não encontrados. A lógica do menu lateral pode não funcionar."
    );
  }

  // Lógica do Dropdown de Exportação (fechar ao clicar fora)
  window.onclick = function (event) {
    // Verifica se o clique não foi dentro do botão de exportação ou do próprio dropdown
    if (
      !event.target.matches(".btn-export") &&
      !event.target.closest(".dropdown-export")
    ) {
      const dropdowns = document.getElementsByClassName("dropdown-content");
      for (let i = 0; i < dropdowns.length; i++) {
        const openDropdown = dropdowns[i];
        if (openDropdown.classList.contains("show")) {
          openDropdown.classList.remove("show");
        }
      }
    }
  };

  // Lógica para mostrar/ocultar campo de cripto na operação
  document.getElementById("operacao")?.addEventListener("change", function () {
    const criptoGroup = document.getElementById("cripto-group");
    if (criptoGroup) {
      criptoGroup.style.display =
        this.value === "compra_cripto" ? "block" : "none";
    }
  });

  // Inicialização do Gráfico Chart.js
  const graficoCanvas = document.getElementById("grafico-canvas");
  if (graficoCanvas) {
    const ctx = graficoCanvas.getContext("2d");
    const moedaSelecionadaElement = document.getElementById("cripto");
    const moedaSelecionada =
      moedaSelecionadaElement &&
      moedaSelecionadaElement.options[moedaSelecionadaElement.selectedIndex]
        ? moedaSelecionadaElement.options[moedaSelecionadaElement.selectedIndex]
            .text
        : "Criptomoeda";

    new Chart(ctx, {
      type: "line",
      data: {
        labels: labels, // Usando a variável global populada via Jinja2
        datasets: [
          {
            label: `Preço do ${moedaSelecionada} (R$)`,
            data: dados, // Usando a variável global populada via Jinja2
            borderColor: "rgba(75, 192, 192, 1)",
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            borderWidth: 2,
            tension: 0.3,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                return `R$ ${context.parsed.y.toFixed(2)}`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: function (value) {
                return "R$ " + value.toFixed(2);
              },
            },
          },
        },
      },
    });
  } else {
    console.warn(
      "Canvas 'grafico-canvas' não encontrado. O gráfico não será inicializado."
    );
  }

  // Lógica do Botão de Alternar Detalhes da Carteira
  const btnToggleCarteira = document.getElementById("btn-toggle-carteira");
  const carteiraDetalhes = document.getElementById("carteira-detalhes");

  if (btnToggleCarteira && carteiraDetalhes) {
    btnToggleCarteira.addEventListener("click", () => {
      const isVisible = carteiraDetalhes.style.display === "block";
      carteiraDetalhes.style.display = isVisible ? "none" : "block";
      btnToggleCarteira.innerHTML = isVisible
        ? '<i class="fas fa-eye"></i> Ver Detalhes da Carteira'
        : '<i class="fas fa-eye-slash"></i> Ocultar Detalhes da Carteira';
    });
  } else {
    console.warn(
      "Elementos #btn-toggle-carteira ou #carteira-detalhes não encontrados. A lógica de alternância da carteira pode não funcionar."
    );
  }

  // Lógica dos Alertas Modais
  const alertModal = document.getElementById("alertModal");
  const alerts = document.querySelectorAll(".alert-container .alert");

  if (alerts.length > 0 && alertModal) {
    alertModal.style.display = "flex";

    alerts.forEach((alert) => {
      const closeBtn = alert.querySelector(".close-alert-btn");
      if (closeBtn) {
        closeBtn.addEventListener("click", () => {
          alert.remove();
          if (
            document.querySelectorAll(".alert-container .alert").length === 0
          ) {
            alertModal.style.display = "none";
          }
        });
      }

      // Define um timeout para remover o alerta automaticamente
      setTimeout(() => {
        alert.remove();
        if (document.querySelectorAll(".alert-container .alert").length === 0) {
          alertModal.style.display = "none";
        }
      }, 5000); // Alerta desaparece após 5 segundos
    });

    // Fecha o modal de alerta ao clicar fora dele
    alertModal.addEventListener("click", (event) => {
      if (event.target === alertModal) {
        alertModal.style.display = "none";
        alerts.forEach((alert) => alert.remove()); // Remove todos os alertas ao fechar o modal
      }
    });
  } else {
    // Se não houver alertas ou o modal não existir, garante que o modal esteja oculto
    if (alertModal) {
      alertModal.style.display = "none";
    }
  }
});
