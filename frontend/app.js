const SAMPLE = {
  light_lux: { label: 'Light', value: 1240, unit: 'lux' },
  air_humidity: { label: 'Air humidity', value: 62, unit: '%' },
  air_temp: { label: 'Air temp', value: 23.6, unit: 'c' },
  soil_moisture: { label: 'Soil moisture', value: 38, unit: '%' },
  co2: { label: 'CO2', value: 640, unit: 'ppm' },
  pressure: { label: 'Pressure', value: 1008, unit: 'hpa' },
  nutrient: { label: 'Nutrient', value: 1.4, unit: 'ec' }
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
    ['air_temp', 23.6, 'c', '2025-02-01 10:10'],
    ['air_humidity', 62, '%', '2025-02-01 10:10'],
    ['co2', 640, 'ppm', '2025-02-01 10:10'],
    ['soil_moisture', 38, '%', '2025-02-01 10:10'],
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
    { title: 'CO2 high', detail: 'Value 980 ppm', time: '10:05' },
    { title: 'Soil moisture low', detail: 'Value 22%', time: '09:40' },
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
