window.addEventListener('DOMContentLoaded', () => {
  const datePicker = document.getElementById('datePicker');
  const today = new Date().toISOString().split('T')[0];
  datePicker.value = today;
  datePicker.min = today;

  const timeGrid = document.getElementById('timeGrid');
  const cabinsList = document.getElementById('cabinsList');

  // Gera slots de INTERVAL em INTERVAL
  const slots = [];
  for (let h = HOUR_START; h <= HOUR_END; h++) {
    for (let m = 0; m < 60; m += INTERVAL) {
      if (h === HOUR_END && m > 30) break;
      const mm = m === 0 ? '00' : String(m).padStart(2,'0');
      slots.push(`${String(h).padStart(2,'0')}:${mm}`);
    }
  }

  // Renderiza botões
  slots.forEach(slot => {
    const btn = document.createElement('button');
    btn.textContent = slot;
    btn.addEventListener('click', () => loadAvailable(datePicker.value, slot));
    timeGrid.appendChild(btn);
  });

  // limpa lista ao trocar data
  datePicker.addEventListener('change', () => cabinsList.innerHTML = '');

  async function loadAvailable(dateIso, slot) {
    cabinsList.innerHTML = '<p>Carregando...</p>';
    const resp = await fetch(`/api/available/${dateIso}/${slot}`);
    const data = resp.ok ? await resp.json() : [];
    renderCabins(data, dateIso, slot);
  }

  function renderCabins(cabins, dateIso, slot) {
    cabinsList.innerHTML = '';
    if (cabins.length === 0) {
      cabinsList.innerHTML = '<p>Nenhuma cabine disponível.</p>';
      return;
    }
    cabins.forEach(c => {
      const div = document.createElement('div');
      div.className = 'produtos';
      div.innerHTML = `
        <h3>${c.nome}</h3>
        <img src="/static/images/${c.imagem}" alt="${c.nome}" width="100%">
        <p>R$ ${c.valor_hora}/h</p>
        <a href="/reserve/${c.id}/${dateIso}/${slot}" class="btn">Reservar</a>
      `;
      cabinsList.appendChild(div);
    });
  }
});
