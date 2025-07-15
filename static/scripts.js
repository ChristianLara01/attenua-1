window.addEventListener('DOMContentLoaded', () => {
  const datePicker = document.getElementById('datePicker');
  const today      = new Date().toISOString().split('T')[0];
  datePicker.value = today;
  datePicker.min   = today;

  const timeGrid   = document.getElementById('timeGrid');
  const cabinsList = document.getElementById('cabinsList');

  // Gera os slots de horário com base nas variáveis globais
  const slots = [];
  for (let h = HOUR_START; h <= HOUR_END; h++) {
    for (let m = 0; m < 60; m += INTERVAL) {
      if (h === HOUR_END && m > 30) break;
      const mm = m === 0 ? '00' : String(m).padStart(2,'0');
      slots.push(`${String(h).padStart(2,'0')}:${mm}`);
    }
  }

  // Cria um botão para cada slot
  slots.forEach(slot => {
    const btn = document.createElement('button');
    btn.textContent = slot;
    btn.className   = 'time-btn';
    btn.addEventListener('click', () => {
      if (!btn.disabled) loadAvailable(datePicker.value, slot);
    });
    timeGrid.appendChild(btn);
  });

  // Reexecuta a verificação de disponibilidade quando a data muda
  datePicker.addEventListener('change', () => {
    cabinsList.innerHTML = '';
    checkSlots(datePicker.value);
  });

  // Verifica slots na carga inicial
  checkSlots(today);

  /**
   * Percorre cada botão de slot e desabilita se não houver cabine livre.
   */
  async function checkSlots(dateIso) {
    const buttons = Array.from(timeGrid.querySelectorAll('button'));
    for (const btn of buttons) {
      const slot = btn.textContent;
      try {
        const resp = await fetch(`/api/available/${dateIso}/${slot}`);
        if (resp.ok) {
          const cabins = await resp.json();
          btn.disabled = (cabins.length === 0);
        } else {
          btn.disabled = true;
        }
      } catch (e) {
        console.error('Erro ao verificar slot', slot, e);
        btn.disabled = true;
      }
    }
  }

  /**
   * Carrega e renderiza cabines disponíveis para um dia+slot selecionados.
   */
  async function loadAvailable(dateIso, slot) {
    cabinsList.innerHTML = '<p>Carregando cabines...</p>';
    try {
      const resp = await fetch(`/api/available/${dateIso}/${slot}`);
      if (resp.ok) {
        const data = await resp.json();
        renderCabins(data, dateIso, slot);
      } else {
        cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
      }
    } catch (e) {
      console.error('Erro ao carregar cabines disponíveis:', e);
      cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
    }
  }

  /**
   * Gera os cards de cabine na tela.
   */
  function renderCabins(cabins, dateIso, slot) {
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
});
