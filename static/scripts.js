// Quantidade de dias a exibir (hoje + próximos N‑1 dias)
const DAYS_COUNT = 7;

window.addEventListener('DOMContentLoaded', () => {
  const dayGrid   = document.getElementById('dayGrid');
  const cabinsList= document.getElementById('cabinsList');
  let selectedDateIso;

  // 1) Gera array de datas ISO e labels (“DD/MM”)
  const dates = [];
  const today = new Date();
  for (let i = 0; i < DAYS_COUNT; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const iso = d.toISOString().split('T')[0]; // YYYY‑MM‑DD
    const day = d.getDate().toString().padStart(2,'0');
    const mon = (d.getMonth()+1).toString().padStart(2,'0');
    dates.push({ iso, label: `${day}/${mon}` });
  }

  // 2) Renderiza botões de dia
  dates.forEach(({ iso, label }, idx) => {
    const btn = document.createElement('button');
    btn.innerHTML = `<span class="weekday">${label}</span>`;
    btn.dataset.iso = iso;
    btn.addEventListener('click', () => {
      // Marca ativo
      dayGrid.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      // Atualiza data e recarrega slots
      selectedDateIso = iso;
      loadSlots(selectedDateIso);
      cabinsList.innerHTML = '';
    });
    dayGrid.appendChild(btn);

    // Seleciona hoje por padrão
    if (idx === 0) {
      btn.classList.add('active');
      selectedDateIso = iso;
    }
  });

  // 3) Primeira carga de slots
  loadSlots(selectedDateIso);
});

/**
 * Carrega e renderiza os botões de horário
 * com UMA SÓ requisição ao servidor.
 */
async function loadSlots(dateIso) {
  const timeGrid = document.getElementById('timeGrid');
  timeGrid.innerHTML = '<p>Carregando horários…</p>';

  try {
    // Única chamada que retorna todos os slots com disponibilidade
    const resp = await fetch(`/api/available_slots/${dateIso}`);
    const slotsData = resp.ok ? await resp.json() : [];
    
    // Renderiza apenas depois de receber tudo
    timeGrid.innerHTML = '';
    for (const { slot, available } of slotsData) {
      const btn = document.createElement('button');
      btn.textContent = slot;
      btn.disabled = !available;
      btn.className = 'time-btn';
      if (available) {
        btn.addEventListener('click', () => loadAvailable(dateIso, slot));
      }
      timeGrid.appendChild(btn);
    }
  } catch (e) {
    console.error('Erro ao carregar slots:', e);
    timeGrid.innerHTML = '<p>Erro ao carregar horários.</p>';
  }
}

/**
 * Busca e renderiza as cabines livres para o slot escolhido
 */
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

/**
 * Monta os cards de cabine na tela
 */
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
