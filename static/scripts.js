document.addEventListener('DOMContentLoaded', () => {
  const dayButtons     = document.querySelectorAll('.day-btn');
  const clockContainer = document.getElementById('timeGrid');
  const modal          = document.getElementById('cabinsModal');
  const cabinsList     = document.getElementById('cabinsList');
  const closeBtn       = document.querySelector('.close-btn');
  let selectedDate     = null;

  // Preseleciona o primeiro dia
  if (dayButtons.length) {
    selectedDate = dayButtons[0].dataset.iso;
    dayButtons[0].classList.add('active');
  }

  // Clique em um dia
  dayButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDate = btn.dataset.iso;
      loadSlots();
    });
  });

  // Carrega slots e posiciona em círculo
  async function loadSlots() {
    clockContainer.innerHTML = '';
    try {
      const resp = await fetch(`/api/available_slots/${selectedDate}`);
      const slotsData = await resp.ok ? await resp.json() : [];
      const n = slotsData.length;
      const radius = 45; // %

      slotsData.forEach(({ slot, available }, i) => {
        const btn = document.createElement('button');
        btn.textContent = slot;
        if (!available) btn.disabled = true;

        const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
        const x = 50 + Math.cos(angle) * radius;
        const y = 50 + Math.sin(angle) * radius;
        btn.style.left = `${x}%`;
        btn.style.top  = `${y}%`;

        btn.addEventListener('click', () => {
          clockContainer.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
          openModal(slot);
        });

        clockContainer.appendChild(btn);
      });
    } catch (e) {
      console.error(e);
      clockContainer.innerHTML = '<p>Erro ao carregar horários.</p>';
    }
  }

  // Abre modal de cabines
  async function openModal(slot) {
    cabinsList.innerHTML = '';
    try {
      const resp = await fetch(`/available/${selectedDate}/${encodeURIComponent(slot)}`);
      const cabins = await resp.ok ? await resp.json() : [];
      if (!cabins.length) {
        cabinsList.innerHTML = '<p>Nenhuma cabine disponível.</p>';
      } else {
        cabins.forEach(c => {
          const card = document.createElement('div');
          card.className = 'cabin-card';
          card.innerHTML = `
            <h4>${c.nome}</h4>
            <img src="/static/images/${c.imagem}" alt="${c.nome}">
            <p>R$ ${c.valor_hora}/h</p>
            <a class="btn"
               href="/reserve/${c.id}/${selectedDate}/${encodeURIComponent(slot)}">
              Reservar
            </a>
          `;
          cabinsList.appendChild(card);
        });
      }
      modal.classList.add('visible');
    } catch (e) {
      console.error(e);
      cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
      modal.classList.add('visible');
    }
  }

  // Fecha modal
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('visible');
  });

  // Carrega slots iniciais
  if (selectedDate) loadSlots();
});
