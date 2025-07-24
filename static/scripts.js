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

  // Ao clicar em um dia, marca e recarrega
  dayButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDate = btn.dataset.iso;
      loadSlots();
    });
  });

  // Carrega e posiciona os slots em formato de relógio
  async function loadSlots() {
    clockContainer.innerHTML = '';
    console.log('Carregando horários para', selectedDate);

    // datas e hora atuais para desabilitar slots do passado
    const now     = new Date();
    const today   = now.toISOString().slice(0,10);

    // tenta o endpoint com /api
    let resp = await fetch(`/api/available_slots/${selectedDate}`);
    if (!resp.ok) resp = await fetch(`/available_slots/${selectedDate}`);
    if (!resp.ok) {
      clockContainer.innerHTML = '<p>Erro ao carregar horários.</p>';
      return;
    }

    const slotsData = await resp.json();
    const n         = slotsData.length;
    const radius    = 40; // % do container, mantém

    // calcula diâmetro das bolinhas:
    const maxD = 40;  // px, quando poucos slots
    const minD = 20;  // px, quando muitos slots
    // escala linear simples: quanto mais slots, menor o diâmetro
    const dia = Math.max(minD, Math.min(maxD, Math.round(maxD * (10 / n))));

    slotsData.forEach(({ slot, available }, i) => {
      const btn = document.createElement('button');
      btn.textContent = slot;

      // parse do horário de slot
      const [hh, mm] = slot.split(':').map(Number);
      const slotDate = new Date(`${selectedDate}T${slot}:00`);

      // desabilita se indisponível ou se for passado
      const isPast = (selectedDate < today) ||
        (selectedDate === today && slotDate < now);
      if (!available || isPast) {
        btn.disabled = true;
        btn.classList.add('past');
      }

      // estilo de tamanho e posicionamento
      btn.style.width  = `${dia}px`;
      btn.style.height = `${dia}px`;
      btn.style.borderRadius = '50%';

      const angle = (i / n) * 2 * Math.PI - Math.PI/2;
      const x     = 50 + Math.cos(angle) * radius;
      const y     = 50 + Math.sin(angle) * radius;
      btn.style.left = `${x}%`;
      btn.style.top  = `${y}%`;

      btn.addEventListener('click', () => {
        clockContainer.querySelectorAll('button')
          .forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        openModal(slot);
      });

      clockContainer.appendChild(btn);
    });
  }

  // Reabre modal de cabines
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

  // inicial
  if (selectedDate) loadSlots();
});
