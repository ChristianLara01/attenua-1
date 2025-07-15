window.addEventListener('DOMContentLoaded', () => {
  const datePicker = document.getElementById('datePicker');
  const today = new Date().toISOString().split('T')[0];

  // Inicializa o date picker
  datePicker.value = today;
  datePicker.min   = today;

  // Ao mudar a data, recarrega os horários
  datePicker.addEventListener('change', () => {
    document.getElementById('cabinsList').innerHTML = '';
    loadSlots(datePicker.value);
  });

  // Carrega slots pela primeira vez
  loadSlots(today);
});

async function loadSlots(dateIso) {
  const timeGrid   = document.getElementById('timeGrid');
  const cabinsList = document.getElementById('cabinsList');

  // Exibe loading
  timeGrid.innerHTML = '<p>Carregando horários…</p>';

  // Gera array de slots no intervalo configurado
  const slots = [];
  for (let h = HOUR_START; h <= HOUR_END; h++) {
    for (let m = 0; m < 60; m += INTERVAL) {
      if (h === HOUR_END && m > 30) break;
      const mm = m === 0 ? '00' : String(m).padStart(2, '0');
      slots.push(`${String(h).padStart(2, '0')}:${mm}`);
    }
  }

  // Para cada slot, busca disponibilidade em paralelo
  const checks = slots.map(async slot => {
    try {
      const resp = await fetch(`/api/available/${dateIso}/${slot}`);
      if (resp.ok) {
        const cabins = await resp.json();
        return { slot, available: cabins.length > 0 };
      }
    } catch (e) {
      console.error('Erro ao verificar slot', slot, e);
    }
    return { slot, available: false };
  });

  // Aguarda todas as verificações
  const results = await Promise.all(checks);

  // Renderiza botões de slot somente depois de tudo pronto
  timeGrid.innerHTML = '';
  results.forEach(({ slot, available }) => {
    const btn = document.createElement('button');
    btn.textContent  = slot;
    btn.disabled     = !available;
    btn.className    = 'time-btn';
    btn.addEventListener('click', () => {
      if (available) loadAvailable(dateIso, slot);
    });
    timeGrid.appendChild(btn);
  });
}

async function loadAvailable(dateIso, slot) {
  const cabinsList = document.getElementById('cabinsList');
  cabinsList.innerHTML = '<p>Carregando cabines…</p>';

  try {
    const resp = await fetch(`/api/available/${dateIso}/${slot}`);
    if (resp.ok) {
      const cabins = await resp.json();
      renderCabins(cabins, dateIso, slot);
      return;
    }
  } catch (e) {
    console.error('Erro ao carregar cabines disponíveis:', e);
  }
  cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
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
