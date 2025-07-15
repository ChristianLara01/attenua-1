document.addEventListener('DOMContentLoaded', () => {
  // Configurações para o seletor de data
  const datePicker = document.getElementById('datePicker');
  const today = new Date().toISOString().split('T')[0];
  datePicker.setAttribute('min', today);

  // Elementos da página
  const timeGrid = document.getElementById('timeGrid');
  const cabinsDiv = document.getElementById('cabinsList');

  // Gera slots de 30 min de 09:00 a 19:30
  function pad(n) { return n.toString().padStart(2, '0'); }
  const slots = [];
  for (let h = 9; h <= 19; h++) {
    for (let m = 0; m < 60; m += 30) {
      if (h === 19 && m > 30) break;
      slots.push(`${pad(h)}:${m === 0 ? '00' : '30'}`);
    }
  }

  // Cria botões de horário
  slots.forEach(slot => {
    const btn = document.createElement('button');
    btn.textContent = slot;
    btn.className = 'time-btn';
    btn.addEventListener('click', () => loadAvailable(datePicker.value, slot));
    timeGrid.appendChild(btn);
  });

  // Busca cabines disponíveis e renderiza
  async function loadAvailable(day, slot) {
    if (!day) { alert('Selecione um dia primeiro.'); return; }
    const resp = await fetch(`/available/${day}/${slot}`);
    if (!resp.ok) {
      console.error('Erro ao buscar cabines disponíveis');
      return;
    }
    const cabins = await resp.json();
    renderCabins(cabins, day, slot);
  }

  // Renderiza cards de cabines
  function renderCabins(cabins, day, slot) {
    cabinsDiv.innerHTML = '';
    if (cabins.length === 0) {
      cabinsDiv.innerHTML = '<p>Nenhuma cabine disponível nesse horário.</p>';
      return;
    }
    cabins.forEach(c => {
      const card = document.createElement('div');
      card.className = 'produtos';
      card.innerHTML = `
        <h2>${c.nome}</h2>
        <div class="card">
          <div class="coluna1">
            <img class="custom-image ${c.image_class}" src="/static/images/${c.imagem}" alt="${c.nome}">
          </div>
          <div class="coluna2">
            <p>R$ ${c.valor_hora}/h</p>
            <a href="/reserve/${c.id}/${day}/${slot}" class="btn">Reservar</a>
          </div>
        </div>`;
      cabinsDiv.appendChild(card);
    });
  }
});
