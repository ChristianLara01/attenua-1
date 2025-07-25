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
    clockContainer.innerHTML = '';
    const now   = new Date();
    const today = now.toISOString().slice(0,10);

    // busca slots
    let resp = await fetch(`/api/available_slots/${selectedDate}`);
    if (!resp.ok) resp = await fetch(`/available_slots/${selectedDate}`);
    if (!resp.ok) {
      clockContainer.innerHTML = '<p>Erro ao carregar horários.</p>';
      return;
    }
    const slotsData = await resp.json();
    const n         = slotsData.length;

    // cálculo do raio em px (40% do container)
    const containerSize = clockContainer.clientWidth;
    const radiusPercent = 40; // mesmo do CSS: 40%
    const radiusPx      = containerSize * (radiusPercent / 100);

    // diâmetro de cada bolinha = comprimento da corda de ângulo 2π/n
    let diameter = 2 * radiusPx * Math.sin(Math.PI / n);

    // opcional: limitar min/max para ficar sempre legível
    const MIN_D = 24;
    const MAX_D = 60;
    diameter = Math.max(MIN_D, Math.min(MAX_D, diameter));

    slotsData.forEach(({ slot, available }, i) => {
      const btn = document.createElement('button');
      btn.textContent = slot;

      // desabilita slots já passados
      const [hh, mm] = slot.split(':').map(Number);
      const slotDate = new Date(`${selectedDate}T${slot}:00`);
      const isPast   = (selectedDate < today) || (selectedDate === today && slotDate < now);
      if (!available || isPast) {
        btn.disabled = true;
      }

      // aplica tamanho e posicionamento
      btn.style.width        = `${diameter}px`;
      btn.style.height       = `${diameter}px`;
      btn.style.borderRadius = '50%';
      const angle = (i / n) * 2 * Math.PI - Math.PI/2;
      const x     = 50 + Math.cos(angle) * radiusPercent;
      const y     = 50 + Math.sin(angle) * radiusPercent;
      btn.style.left = `${x}%`;
      btn.style.top  = `${y}%`;

      btn.addEventListener('click', () => {
        clockContainer.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
        if (!btn.disabled) {
          btn.classList.add('selected');
          openModal(slot);
        }
      });

      clockContainer.appendChild(btn);
    });
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
