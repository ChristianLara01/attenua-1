document.addEventListener('DOMContentLoaded', () => {
  const days = Array.from(document.querySelectorAll('.day-btn'));
  const timeGrid = document.getElementById('timeGrid');
  const modal = document.getElementById('cabinsModal');
  const cabinsList = document.getElementById('cabinsList');
  const closeBtn = document.querySelector('.close-btn');
  let selectedDate = days[0].dataset.iso;

  function highlightDay(btn) {
    days.forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    selectedDate = btn.dataset.iso;
    loadSlots();
  }

  days.forEach(btn => {
    btn.addEventListener('click', ()=>highlightDay(btn));
  });
  highlightDay(days[0]);

  async function loadSlots() {
    timeGrid.innerHTML = '<p>Carregando horários…</p>';
    const resp = await fetch(`/api/available_slots/${selectedDate}`);
    const data = await resp.json();
    timeGrid.innerHTML = '';
    data.forEach(({slot,available}) => {
      const b = document.createElement('button');
      b.textContent = slot;
      b.disabled = !available;
      b.addEventListener('click', ()=>openModal(slot));
      timeGrid.appendChild(b);
    });
  }

  async function openModal(slot) {
    const resp = await fetch(`/available/${selectedDate}/${slot}`);
    const cabins = await resp.json();
    cabinsList.innerHTML = '';
    cabins.forEach(c => {
      const d = document.createElement('div');
      d.className = 'cabin-card';
      d.innerHTML = `
        <h4>${c.nome}</h4>
        <img src="/static/images/${c.imagem}" alt="${c.nome}">
        <p>R$ ${c.valor_hora}/h</p>
        <a class="btn" href="/reserve/${c.id}/${selectedDate}/${slot}">Reservar</a>
      `;
      cabinsList.appendChild(d);
    });
    modal.classList.add('visible');
  }

  closeBtn.addEventListener('click', ()=>{
    modal.classList.remove('visible');
  });
});
