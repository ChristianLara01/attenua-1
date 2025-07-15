window.addEventListener('DOMContentLoaded', () => {
  const datePicker = document.getElementById('datePicker');
  const today      = new Date().toISOString().split('T')[0];
  datePicker.value = today;
  datePicker.min   = today;

  const timeGrid  = document.getElementById('timeGrid');
  const cabinsDiv = document.getElementById('cabinsList');

  // Gera slots conforme configuração
  const slots = [];
  for (let h = HOUR_START; h <= HOUR_END; h++) {
    for (let m = 0; m < 60; m += INTERVAL) {
      if (h === HOUR_END && m > 30) break;
      const mm = m === 0 ? '00' : String(m).padStart(2,'0');
      slots.push(`${String(h).padStart(2,'0')}:${mm}`);
    }
  }

  // Cria botões de horário
  slots.forEach(slot => {
    const btn = document.createElement('button');
    btn.textContent = slot;
    btn.className = 'time-btn';
    btn.addEventListener('click', () => loadAvailable(datePicker.value, slot));
    timeGrid.appendChild(btn);
  });

  // Limpa lista ao mudar o dia
  datePicker.addEventListener('change', () => cabinsDiv.innerHTML = '');

  // Busca e renderiza apenas cabines livres
  async function loadAvailable(dateIso, slot) {
    cabinsDiv.innerHTML = '<p>Carregando cabines...</p>';
    const resp = await fetch(`/api/available/${dateIso}/${slot}`);
    if (!resp.ok) {
      cabinsDiv.innerHTML = '<p>Erro ao buscar cabines.</p>';
      return;
    }
    const cabines = await resp.json();
    renderCabins(cabines, dateIso, slot);
  }

  function renderCabins(cabines, dateIso, slot) {
    cabinsDiv.innerHTML = '';
    if (cabines.length === 0) {
      cabinsDiv.innerHTML = '<p>Nenhuma cabine disponível nesse horário.</p>';
      return;
    }
    cabines.forEach(c => {
      const card = document.createElement('div');
      card.className = 'produtos';
      card.innerHTML = `
        <h3>${c.nome}</h3>
        <img src="/static/images/${c.imagem}" alt="${c.nome}" width="100%">
        <p>R$ ${c.valor_hora}/h</p>
        <a href="/reserve/${c.id}/${dateIso}/${slot}" class="btn">Reservar</a>
      `;
      cabinsDiv.appendChild(card);
    });
  }
});
