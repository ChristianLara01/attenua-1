// static/scripts.js

document.addEventListener('DOMContentLoaded', () => {
  const dayButtons     = document.querySelectorAll('.day-btn');
  const clockContainer = document.getElementById('timeGrid');
  const modal          = document.getElementById('cabinsModal');
  const cabinsList     = document.getElementById('cabinsList');
  const closeBtn       = document.querySelector('.close-btn');
  let selectedDate     = null;

  // Preseleciona o primeiro dia
  if (dayButtons.length > 0) {
    selectedDate = dayButtons[0].dataset.iso;
    dayButtons[0].classList.add('active');
  }

  // Ao clicar em um dia, marca-o e recarrega os slots
  dayButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDate = btn.dataset.iso;
      loadSlots();
    });
  });

  // Função para carregar e posicionar os slots em formato de relógio
  async function loadSlots() {
    clockContainer.innerHTML = '';
    console.log('Carregando horários para', selectedDate);

    // 1) Tenta o endpoint com /api
    let resp = await fetch(`/api/available_slots/${selectedDate}`);
    if (!resp.ok) {
      console.warn('Falha em /api/available_slots, status', resp.status, '- tentando /available_slots...');
      // 2) Fallback se o primeiro endpoint não existir
      resp = await fetch(`/available_slots/${selectedDate}`);
    }

    if (!resp.ok) {
      console.error('Ambos endpoints falharam:', resp.status);
      clockContainer.innerHTML = '<p>Erro ao carregar horários.</p>';
      return;
    }

    try {
      const slotsData = await resp.json();
      const n         = slotsData.length;
      const radius    = 40; // em %

      slotsData.forEach(({ slot, available }, i) => {
        const btn = document.createElement('button');
        btn.textContent = slot;
        if (!available) btn.disabled = true;

        // posiciona em círculo
        const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
        const x     = 50 + Math.cos(angle) * radius;
        const y     = 50 + Math.sin(angle) * radius;
        btn.style.left = `${x}%`;
        btn.style.top  = `${y}%`;

        btn.addEventListener('click', () => {
          // destaque do slot selecionado
          clockContainer.querySelectorAll('button')
            .forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
          openModal(slot);
        });

        clockContainer.appendChild(btn);
      });
    } catch (e) {
      console.error('Erro ao processar JSON dos horários:', e);
      clockContainer.innerHTML = '<p>Erro interno ao processar horários.</p>';
    }
  }

  // Função para abrir o modal listando cabines disponíveis para o slot
  async function openModal(slot) {
    cabinsList.innerHTML = '';
    console.log('Buscando cabines para', selectedDate, slot);
    try {
      const resp = await fetch(`/available/${selectedDate}/${encodeURIComponent(slot)}`);
      if (!resp.ok) throw new Error(`Status ${resp.status}`);
      const cabins = await resp.json();

      if (cabins.length === 0) {
        cabinsList.innerHTML = '<p>Nenhuma cabine disponível.</p>';
      } else {
        cabins.forEach(c => {
          const card = document.createElement('div');
          card.className = 'cabin-card';
          card.innerHTML = `
            <h4>${c.nome}</h4>
            <img src="/static/images/${c.imagem}" alt="${c.nome}">
            <a class="btn"
               href="/reserve/${c.id}/${selectedDate}/${encodeURIComponent(slot)}">
              Reservar
            </a>
          `;
          cabinsList.appendChild(card);
        });
      }

      modal.classList.add('visible');
    } catch (error) {
      console.error('Erro ao buscar cabines:', error);
      cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
      modal.classList.add('visible');
    }
  }

  // Fecha o modal ao clicar no X
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('visible');
  });

  // Carrega slots na inicialização
  if (selectedDate) {
    loadSlots();
  }
});
