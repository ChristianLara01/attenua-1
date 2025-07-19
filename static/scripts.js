// static/scripts.js

document.addEventListener('DOMContentLoaded', () => {
  const dayButtons = document.querySelectorAll('.day-btn');
  const timeGrid   = document.getElementById('timeGrid');
  const modal      = document.getElementById('cabinsModal');
  const cabinsList = document.getElementById('cabinsList');
  const closeBtn   = document.querySelector('.close-btn');
  let selectedDate = null;

  // Marca o primeiro dia como ativo e define selectedDate
  if (dayButtons.length > 0) {
    dayButtons[0].classList.add('active');
    selectedDate = dayButtons[0].dataset.iso;
  }

  // Ao clicar num dia: destaca e recarrega horários
  dayButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      dayButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDate = btn.dataset.iso;
      loadSlots();
    });
  });

  // Carrega e exibe botões de horário para a data selecionada
  async function loadSlots() {
    timeGrid.innerHTML = '<p>Carregando horários…</p>';
    try {
      const resp = await fetch(`/api/available_slots/${selectedDate}`);
      if (!resp.ok) throw new Error('Falha ao buscar horários');
      const slots = await resp.json();

      timeGrid.innerHTML = '';
      slots.forEach(({ slot, available }) => {
        const btn = document.createElement('button');
        btn.textContent = slot;
        btn.disabled   = !available;
        btn.addEventListener('click', () => openModal(slot));
        timeGrid.appendChild(btn);
      });
    } catch (err) {
      console.error(err);
      timeGrid.innerHTML = '<p>Erro ao carregar horários.</p>';
    }
  }

  // Abre o modal e carrega as cabines disponíveis para o slot clicado
  async function openModal(slot) {
    try {
      const resp = await fetch(`/available/${selectedDate}/${slot}`);
      if (!resp.ok) throw new Error('Falha ao buscar cabines');
      const cabins = await resp.json();

      cabinsList.innerHTML = '';
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
            <a class="btn"
               href="/reserve/${c.id}/${selectedDate}/${slot}">
              Reservar
            </a>
          `;
          cabinsList.appendChild(card);
        });
      }
      modal.classList.add('visible');
    } catch (err) {
      console.error(err);
    }
  }

  // Fecha o modal ao clicar no “×”
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('visible');
  });

  // Carrega horários iniciais
  if (selectedDate) loadSlots();
});
