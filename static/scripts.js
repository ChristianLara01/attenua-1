document.addEventListener("DOMContentLoaded", () => {
  // Date picker at top of catalog page
  const datePicker = document.getElementById('datePicker');
  const todayISO = new Date().toISOString().split('T')[0];

  if (datePicker) {
    datePicker.setAttribute('min', todayISO);
    datePicker.value = todayISO;
    datePicker.addEventListener('change', loadAllSchedules);
  }

  loadAllSchedules();
});

/**
 * Load schedules for all cabins based on selected date
 */
function loadAllSchedules() {
  const datePicker = document.getElementById('datePicker');
  const selectedISO = datePicker ? datePicker.value : new Date().toISOString().split('T')[0];
  const formattedDate = formatDate(selectedISO);

  document.querySelectorAll('.produtos').forEach(div => {
    const cabinId = div.getAttribute('data-id');
    const scheduleContainer = div.querySelector('.schedule');
    if (scheduleContainer) {
      scheduleContainer.innerHTML = ''; // Clear previous
      loadCabinSchedule(cabinId, formattedDate, scheduleContainer);
    }
  });
}

/**
 * Convert yyyy-mm-dd to dd-mm-yyyy
 */
function formatDate(isoDate) {
  const [year, month, day] = isoDate.split('-');
  return `${day}-${month}-${year}`;
}

/**
 * Fetch cabin data and render its available slots
 */
function loadCabinSchedule(cabinId, dia, container) {
  fetch('/data/cabins')
    .then(resp => resp.json())
    .then(data => {
      const cabin = data.find(c => c.id === parseInt(cabinId));
      if (!cabin) return;

      // Collect booked hours for this date
      const booked = (cabin.agendamentos || [])
        .filter(a => a.dia === dia)
        .map(a => a.hora);

      renderTable(dia, cabinId, booked, container);
    })
    .catch(err => console.error('Erro ao carregar cabines:', err));
}

/**
 * Render a table of hours from 09:00 to 17:00
 */
function renderTable(dia, cabinId, bookedHours, container) {
  const table = document.createElement('table');

  for (let h = 9; h < 18; h++) {
    const hourStr = String(h).padStart(2, '0') + ':00';
    const row = document.createElement('tr');
    const cell = document.createElement('td');

    cell.textContent = hourStr;
    if (bookedHours.includes(hourStr)) {
      cell.classList.add('booked');
    } else {
      cell.classList.add('clickable');
      cell.addEventListener('click', () => {
        window.location.href = `/reserve/${cabinId}/${dia}/${hourStr}`;
      });
    }

    row.appendChild(cell);
    table.appendChild(row);
  }

  container.appendChild(table);
}

/**
 * Function for access code verification
 */
function redirecionar() {
  const codigo = document.getElementById('codigo').value;
  fetch(`/verificar_senha/${encodeURIComponent(codigo)}`)
    .then(res => res.text())
    .then(msg => {
      alert(msg === 'Liberado' ? 'Acesso liberado!' : 'Código inválido');
    })
    .catch(err => console.error('Erro ao verificar código:', err));
}
