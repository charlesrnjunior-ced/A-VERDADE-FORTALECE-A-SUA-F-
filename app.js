const API_BASE = "";

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    document.getElementById("resultado-container").classList.add("hidden");
  });
});

document.getElementById("btn-exemplo-fake").addEventListener("click", () => {
  document.getElementById("input-url").value = "";
  document.getElementById("input-texto").value =
    "URGENTE REPASSEM NOS GRUPOS DA IGREJA: Foi aprovado decreto secreto para fechar todas as igrejas evangélicas e proibir a leitura da Bíblia no Brasil após as eleições de 2022. Pastores já estão sendo intimados.";
});

document.getElementById("btn-exemplo-real").addEventListener("click", () => {
  document.getElementById("input-url").value = "https://www.tse.jus.br";
  document.getElementById("input-texto").value =
    "O Tribunal Superior Eleitoral (TSE) esclarece que são falsas as mensagens que afirmam que igrejas serão fechadas após as eleições. A liberdade religiosa e de culto é garantida pela Constituição Federal de 1988.";
});

const uploadBox = document.getElementById("upload-box");
const inputVideo = document.getElementById("input-video");
const nomeArquivo = document.getElementById("nome-arquivo");

uploadBox.addEventListener("click", () => inputVideo.click());
inputVideo.addEventListener("change", () => {
  if (inputVideo.files.length > 0) {
    nomeArquivo.textContent = `Arquivo selecionado: ${inputVideo.files[0].name}`;
  }
});

function mostrarLoading(ativo, mensagem = "") {
  const el = document.getElementById("loading");
  const txt = document.getElementById("loading-text");
  if (ativo) {
    txt.textContent = mensagem;
    el.classList.remove("hidden");
    document.getElementById("resultado-container").classList.add("hidden");
  } else {
    el.classList.add("hidden");
  }
}

function classeVeredito(texto) {
  const t = texto.toUpperCase();
  if (t.includes("FALSO") || t.includes("PROVÁVEL VÍDEO GERADO POR IA")) return "veredito-falso";
  if (t.includes("VERDADEIRO") || t.includes("AUTÊNTICO")) return "veredito-verdadeiro";
  return "veredito-alerta";
}

document.getElementById("btn-analisar-texto").addEventListener("click", async () => {
  const texto = document.getElementById("input-texto").value.trim();
  const url = document.getElementById("input-url").value.trim();

  if (!texto && !url) {
    alert("Por favor, insira um texto ou link para verificar.");
    return;
  }

  mostrarLoading(true, "Verificando fatos históricos de 2022 e analisando o discurso...");

  try {
    const resp = await fetch(`${API_BASE}/api/analisar-texto`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto, url }),
    });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.detail || "Erro na análise.");

    const d = json.dados;
    const container = document.getElementById("resultado-container");
    container.innerHTML = `
      <span class="veredito-banner ${classeVeredito(d.veredito)}">${d.veredito} • Risco de Desinformação: ${d.nivel_risco}%</span>
      <p><strong>Parecer da Checagem:</strong> ${d.resumo_executivo}</p>
      <h4>Táticas de Manipulação Identificadas</h4>
      <ul>${d.taticas_detectadas.map((t) => `<li>${t}</li>`).join("")}</ul>
      <h4>Contexto das Eleições de 2022</h4>
      <p>${d.contexto_eleicoes_2022}</p>
      <h4>Orientação para o Leitor</h4>
      <p>${d.dica_educativa}</p>
    `;
    container.classList.remove("hidden");
  } catch (erro) {
    alert(`Falha ao analisar: ${erro.message}`);
  } finally {
    mostrarLoading(false);
  }
});

document.getElementById("btn-analisar-video").addEventListener("click", async () => {
  if (!inputVideo.files.length) {
    alert("Selecione um arquivo de vídeo primeiro.");
    return;
  }

  const formData = new FormData();
  formData.append("video", inputVideo.files[0]);
  formData.append("contexto", document.getElementById("input-contexto-video").value.trim());

  mostrarLoading(true, "Extraindo quadros do vídeo e inspecionando sinais de Inteligência Artificial...");

  try {
    const resp = await fetch(`${API_BASE}/api/analisar-video`, {
      method: "POST",
      body: formData,
    });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.detail || "Erro ao processar vídeo.");

    const d = json.dados;
    const container = document.getElementById("resultado-container");
    container.innerHTML = `
      <span class="veredito-banner ${classeVeredito(d.classificacao)}">${d.classificacao} • Probabilidade de IA: ${d.probabilidade_ia}%</span>
      <p><strong>Laudo Forense Visual:</strong> ${d.resumo_forense}</p>
      <h4>Indicadores Observados nos Quadros</h4>
      <ul>${d.indicadores_visuais.map((i) => `<li>${i}</li>`).join("")}</ul>
      <h4>Alerta Contextual</h4>
      <p>${d.alerta_contextual}</p>
      <h4>Como Confirmar a Autenticidade</h4>
      <p>${d.recomendacao}</p>
    `;
    container.classList.remove("hidden");
  } catch (erro) {
    alert(`Falha ao analisar vídeo: ${erro.message}`);
  } finally {
    mostrarLoading(false);
  }
});
