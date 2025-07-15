// Número de dias a exibir (hoje + próximos N‑1 dias)
const DAYS_COUNT = 7;         

window.addEventListener('DOMContentLoaded', () => {
  const dayGrid   = document.getElementById('dayGrid');
  const cabinsList= document.getElementById('cabinsList');
  let selectedDateIso;

  // 1) Gera array de datas ISO e rótulos
  const dates = [];
  const today = new Date();
  for (let i = 0; i < DAYS_COUNT; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const iso = d.toISOString().split('T')[0];         // "YYYY-MM-DD"
    const day  = d.getDate().toString().padStart(2,'0');
    const mon  = (d.getMonth()+1).toString().padStart(2,'0');
    dates.push({ iso, label: `${day}/${mon}` });
  }

  // 2) Renderiza botões de dia
  dates.forEach(({iso, label}, idx) => {
    const btn = document.createElement('button');
    btn.innerHTML = `<span class="weekday">${label}</span>`;
    btn.dataset.iso = iso;
    btn.addEventListener('click', () => {
      // ativa/desativa estilos
      dayGrid.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      // define data selecionada e carrega horários
      selectedDateIso = iso;
      loadSlots(selectedDateIso);
      cabinsList.innerHTML = '';
    });
    dayGrid.appendChild(btn);

    // pre‑seleciona o primeiro (hoje)
    if (idx === 0) {
      btn.classList.add('active');
      selectedDateIso = iso;
    }
  });

  // 3) Logo na carga inicial, já busca horários de hoje
  loadSlots(selectedDateIso);
});

/**
 * Carrega e exibe botões de horário só depois de checar disponibilidade.
 */
async function loadSlots(dateIso) {
  const timeGrid = document.getElementById('timeGrid');
  timeGrid.innerHTML = '<p>Carregando horários…</p>';

  // gera slots
  const slots = [];
  for (let h = HOUR_START; h <= HOUR_END; h++) {
    for (let m = 0; m < 60; m += INTERVAL) {
      if (h === HOUR_END && m > 30) break;
      const mm = m === 0 ? '00' : String(m).padStart(2,'0');
      slots.push(`${String(h).padStart(2,'0')}:${mm}`);
    }
  }

  // checa todos em paralelo
  const checks = slots.map(async slot => {
    try {
      const resp = await fetch(`/api/available/${dateIso}/${slot}`);
      if (resp.ok) {
        const arr = await resp.json();
        return { slot, available: arr.length > 0 };
      }
    } catch {}
    return { slot, available: false };
  });
  const results = await Promise.all(checks);

  // renderiza botões de horário
  timeGrid.innerHTML = '';
  results.forEach(({slot, available}) => {
    const btn = document.createElement('button');
    btn.textContent = slot;
    btn.disabled = !available;
    btn.addEventListener('click', () => {
      if (available) loadAvailable(dateIso, slot);
    });
    timeGrid.appendChild(btn);
  });
}

/**
 * Exibe as cabines livres para o dia+slot.
 */
async function loadAvailable(dateIso, slot) {
  const cabinsList = document.getElementById('cabinsList');
  cabinsList.innerHTML = '<p>Carregando cabines…</p>';
  try {
    const resp = await fetch(`/api/available/${dateIso}/${slot}`);
    if (resp.ok) {
      const data = await resp.json();
      renderCabins(data, dateIso, slot);
      return;
    }
  } catch {}
  cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
}

function renderCabins(cabins, dateIso, slot) {
  const cabinsList = document.getElementById('cabinsList');
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
