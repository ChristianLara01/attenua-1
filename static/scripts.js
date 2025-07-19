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

  // Ao clicar em um dia, marca e recarrega horários
  dayButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDate = btn.dataset.iso;
      loadSlots();
    });
  });

  // Busca e posiciona os botões de horário no “clock face”
  async function loadSlots() {
    clockContainer.innerHTML = ''; // limpa o relógio

    try {
      const resp = await fetch(`/api/available_slots/${selectedDate}`);
      if (!resp.ok) throw new Error('Falha ao buscar horários');
      const slotsData = await resp.json();

      const n = slotsData.length;
      const radiusPercent = 45; // percentual do raio interno do círculo

      slotsData.forEach(({ slot, available }, i) => {
        const btn = document.createElement('button');
        btn.textContent = slot;
        if (!available) btn.disabled = true;

        // calcula ângulo em radianos (0º no topo)
        const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
        const x = 50 + Math.cos(angle) * radiusPercent;
        const y = 50 + Math.sin(angle) * radiusPercent;
        btn.style.left = `${x}%`;
        btn.style.top  = `${y}%`;

        btn.addEventListener('click', () => {
          // destaca o selecionado
          clockContainer.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
          openModal(slot);
        });

        clockContainer.appendChild(btn);
      });
    } catch (err) {
      console.error(err);
      clockContainer.innerHTML = '<p>Erro ao carregar horários.</p>';
    }
  }

  // Abre modal com as cabines para o slot escolhido
  async function openModal(slot) {
    cabinsList.innerHTML = ''; // limpa lista

    try {
      const resp = await fetch(`/available/${selectedDate}/${slot}`);
      if (!resp.ok) throw new Error('Falha ao buscar cabines');
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
            <p>R$ ${c.valor_hora}/h</p>
            <a class="btn" href="/reserve/${c.id}/${selectedDate}/${slot}">
              Reservar
            </a>
          `;
          cabinsList.appendChild(card);
        });
      }

      modal.classList.add('visible');
    } catch (err) {
      console.error(err);
      cabinsList.innerHTML = '<p>Erro ao carregar cabines.</p>';
      modal.classList.add('visible');
    }
  }

  // Fecha o modal
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('visible');
  });

  // Primeira carga
  if (selectedDate) loadSlots();
});
