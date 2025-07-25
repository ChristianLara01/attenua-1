// static/scripts.js

document.addEventListener('DOMContentLoaded', () => {
  const dayButtons     = document.querySelectorAll('.day-btn');
  const clockContainer = document.getElementById('timeGrid');
  const modal          = document.getElementById('cabinsModal');
  const cabinsList     = document.getElementById('cabinsList');
  const closeBtn       = document.querySelector('.close-btn');
  let selectedDate     = null;

  if (dayButtons.length) {
    selectedDate = dayButtons[0].dataset.iso;
    dayButtons[0].classList.add('active');
  }

  dayButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDate = btn.dataset.iso;
      loadSlots();
    });
  });

  async function loadSlots() {
  const timeGrid = document.getElementById('timeGrid');
  timeGrid.innerHTML = '';
  const now   = new Date();
  const today = now.toISOString().slice(0,10);

  // Busca disponibilidade
  let resp = await fetch(`/api/available_slots/${selectedDate}`);
  if (!resp.ok) resp = await fetch(`/available_slots/${selectedDate}`);
  if (!resp.ok) {
    timeGrid.innerHTML = '<p style="color:#e74c3c;text-align:center;">Erro ao carregar horários.</p>';
    return;
  }
  const slotsData = await resp.json();

  // Divide em Manhã e Tarde
  const morning   = slotsData.filter(s => +s.slot.split(':')[0] < 12);
  const afternoon = slotsData.filter(s => +s.slot.split(':')[0] >= 12);

  function renderSection(title, list) {
    const sec = document.createElement('div');
    sec.className = 'slots-section';
    sec.innerHTML = `<h3>${title}</h3><div class="slots-grid"></div>`;
    const grid = sec.querySelector('.slots-grid');

    list.forEach(({ slot, available }) => {
      const btn = document.createElement('button');
      btn.textContent = slot;

      // Verifica horário passado
      const [hh, mm] = slot.split(':').map(Number);
      const slotDate = new Date(`${selectedDate}T${slot}:00`);
      const isPast = (selectedDate < today) ||
                     (selectedDate === today && slotDate < now);

      if (!available || isPast) btn.disabled = true;

      btn.addEventListener('click', () => {
        if (btn.disabled) return;
        document.querySelectorAll('.slots-grid button')
                .forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        openModal(slot);
      });

      grid.appendChild(btn);
    });

    timeGrid.appendChild(sec);
  }

  renderSection('Manhã', morning);
  renderSection('Tarde', afternoon);
}

  async function openModal(slot) {
    cabinsList.innerHTML = '';
    try {
      const resp = await fetch(`/available/${selectedDate}/${encodeURIComponent(slot)}`);
      const cabins = resp.ok ? await resp.json() : [];
      if (!cabins.length) {
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
            </a>`;
          cabinsList.appendChild(card);
        });
      }
      modal.classList.add('visible');
    } catch {
      cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
      modal.classList.add('visible');
    }
  }

  closeBtn.addEventListener('click', () => {
    modal.classList.remove('visible');
  });

  if (selectedDate) loadSlots();
});
