document.addEventListener("DOMContentLoaded", () => {
  const dayContainer = document.getElementById("dayButtons");
  const timeGrid = document.getElementById("timeGrid");

  if (!dayContainer || !timeGrid) return;

  const today = new Date();
  const dias = 5; // altere para mais/menos dias
  let diasGerados = [];

  for (let i = 0; i < dias; i++) {
    const data = new Date(today);
    data.setDate(today.getDate() + i);
    const diaISO = data.toISOString().split("T")[0];
    diasGerados.push(diaISO);

    const btn = document.createElement("button");
    btn.textContent = diaISO;
    btn.className = "day-btn";
    btn.addEventListener("click", () => carregarHorarios(diaISO));
    dayContainer.appendChild(btn);
  }

  async function carregarHorarios(dia) {
    const resp = await fetch(`/horarios_disponiveis/${dia}`);
    const horarios = await resp.json();
    timeGrid.innerHTML = '';

    horarios.forEach(h => {
      const btn = document.createElement("button");
      btn.textContent = h.hora;
      btn.disabled = !h.disponivel;
      btn.addEventListener("click", () => window.location.href = `/reservation/${dia}/${h.hora}`);
      timeGrid.appendChild(btn);
    });
  }

  // carregar o primeiro dia por padrão
  carregarHorarios(diasGerados[0]);
});
