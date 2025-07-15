window.addEventListener('DOMContentLoaded', () => {
  const datePicker = document.getElementById('datePicker');
  const today      = new Date().toISOString().split('T')[0];
  datePicker.value = today;
  datePicker.min   = today;

  datePicker.addEventListener('change', () => {
    document.getElementById('cabinsList').innerHTML = '';
    loadSlots(datePicker.value);
  });

  // Carrega os botões só UMA vez por data
  loadSlots(today);
});

async function loadSlots(dateIso) {
  const timeGrid = document.getElementById('timeGrid');
  timeGrid.innerHTML = '<p>Carregando horários…</p>';

  try {
    const resp    = await fetch(`/api/available-slots/${dateIso}`);
    const results = resp.ok ? await resp.json() : [];
    timeGrid.innerHTML = '';
    
    results.forEach(({ slot, available }) => {
      const btn = document.createElement('button');
      btn.textContent = slot;
      btn.disabled   = !available;
      btn.className  = 'time-btn';
      btn.addEventListener('click', () => {
        if (available) loadAvailable(dateIso, slot);
      });
      timeGrid.appendChild(btn);
    });
  } catch (e) {
    console.error('Erro ao carregar slots:', e);
    timeGrid.innerHTML = '<p>Erro ao carregar horários.</p>';
  }
}

async function loadAvailable(dateIso, slot) {
  const cabinsList = document.getElementById('cabinsList');
  cabinsList.innerHTML = '<p>Carregando cabines…</p>';

  try {
    const resp    = await fetch(`/api/available/${dateIso}/${slot}`);
    const cabins  = resp.ok ? await resp.json() : [];
    renderCabins(cabins, dateIso, slot);
  } catch (e) {
    console.error('Erro ao carregar cabines:', e);
    cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
  }
}

function renderCabins(cabins, dateIso, slot) {
  const cabinsList = document.getElementById('cabinsList');
  cabinsList.innerHTML = '';

  if (cabins.length === 0) {
    cabinsList.innerHTML = '<p>Nenhuma cabine disponível nesse horário.</p>';
    return;
  }

  cabins.forEach(c => {
    const card = document.createElement('div');
    card.className = 'produtos';
    card.innerHTML = `
      <h3>${c.nome}</h3>
      <img src="/static/images/${c.imagem}" alt="${c.nome}" width="100%">
      <p>R$ ${c.valor_hora}/h</p>
      <a href="/reserve/${c.id}/${dateIso}/${slot}" class="btn">Reservar</a>
    `;
    cabinsList.appendChild(card);
  });
}
