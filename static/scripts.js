document.addEventListener("DOMContentLoaded", () => {
  const dateSelector = document.getElementById('dateSelector');
  const timeGrid = document.getElementById('timeGrid');
  const modal = document.getElementById('cabinsModal');
  const cabinsContent = document.getElementById('cabinsContent');

  const diasExibidos = 5;
  const horarios = ["15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00"];

  let dataSelecionada = null;

  function gerarDatas() {
    const hoje = new Date();
    for (let i = 0; i < diasExibidos; i++) {
      const d = new Date(hoje);
      d.setDate(hoje.getDate() + i);
      const dia = d.toISOString().split('T')[0];

      const btn = document.createElement("button");
      btn.textContent = `${d.getDate()}/${d.getMonth()+1}`;
      btn.addEventListener("click", () => {
        dataSelecionada = dia;
        carregarHorarios();
      });
      dateSelector.appendChild(btn);
    }
  }

  function carregarHorarios() {
    timeGrid.innerHTML = '';
    horarios.forEach(horario => {
      const btn = document.createElement("button");
      btn.textContent = horario;
      btn.addEventListener("click", () => carregarCabines(horario));
      timeGrid.appendChild(btn);
    });
  }

  async function carregarCabines(horario) {
    if (!dataSelecionada) return alert("Selecione uma data");

    const resp = await fetch(`/available/${dataSelecionada}/${horario}`);
    const cabines = await resp.json();

    cabinsContent.innerHTML = '';
    cabines.forEach(cabine => {
      const div = document.createElement("div");
      div.className = "produto";
      div.innerHTML = `
        <h3>${cabine.nome}</h3>
        <img src="/static/images/${cabine.imagem}" alt="${cabine.nome}" style="max-width:100%">
        <p>R$ ${cabine.valor_hora}/h</p>
        <a class="btn" href="/reserve/${cabine.id}?date=${dataSelecionada}&slot=${horario}">Reservar</a>
      `;
      cabinsContent.appendChild(div);
    });

    modal.style.display = "flex";
  }

  gerarDatas();

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });
});
