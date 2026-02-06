const SAMPLE = {
  humidity: { label: 'Humidity', value: 62, unit: '%' },
  temperature: { label: 'Temperature', value: 23.6, unit: 'c' },
  pressure: { label: 'Pressure', value: 1008, unit: 'hpa' },
  soil_ph: { label: 'Soil acidity', value: 6.4, unit: 'ph' }
};

function updateMetrics() {
  document.querySelectorAll('[data-metric]').forEach((card) => {
    const key = card.dataset.metric;
    const data = SAMPLE[key];
    if (!data) return;
    const valueEl = card.querySelector('.metric-value');
    const unitEl = card.querySelector('.metric-unit');
    if (valueEl) valueEl.textContent = data.value;
    if (unitEl) unitEl.textContent = data.unit;
  });

  const lastUpdate = document.getElementById('last-update');
  if (lastUpdate) {
    const now = new Date();
    lastUpdate.textContent = now.toLocaleString();
  }
}

function populateReadings() {
  const table = document.getElementById('readings-body');
  if (!table) return;
  const rows = [
    ['temperature', 23.6, 'c', '2025-02-01 10:10'],
    ['humidity', 62, '%', '2025-02-01 10:10'],
    ['pressure', 1008, 'hpa', '2025-02-01 10:10'],
    ['soil_ph', 6.4, 'ph', '2025-02-01 10:10'],
  ];
  table.innerHTML = rows
    .map(
      (row) =>
        `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td><td>${row[3]}</td></tr>`
    )
    .join('');
}

function populateAlerts() {
  const list = document.getElementById('alert-list');
  if (!list) return;
  const alerts = [
    { title: 'Pressure high', detail: 'Value 1022 hpa', time: '10:05' },
    { title: 'Soil acidity out of range', detail: 'Value 5.2 ph', time: '09:40' },
  ];
  list.innerHTML = alerts
    .map(
      (alert) => `
      <div class="alert-item">
        <div>
          <strong>${alert.title}</strong>
          <span>${alert.detail}</span>
        </div>
        <span class="badge">${alert.time}</span>
      </div>
    `
    )
    .join('');
}

document.addEventListener('DOMContentLoaded', () => {
  updateMetrics();
  populateReadings();
  populateAlerts();
});
