const API_BASE = window.AGROLINK_API_BASE || 'http://localhost:8000/api/v1';

const SENSOR_LABELS_FR = {
  luminosity: 'Luminosite',
  air_humidity: 'Humidite air',
  soil_humidity: 'Humidite sol',
  co2: 'CO2',
  nutrient_index: 'Nutriments',
  pressure: 'Pression',
  heat: 'Chaleur'
};

const SENSOR_HINTS = {
  luminosity: 'Ajuster l eclairage selon la croissance.',
  air_humidity: 'Limiter les stress hydriques et maladies.',
  soil_humidity: 'Piloter l irrigation avec precision.',
  co2: 'Maintenir la photosynthese active.',
  nutrient_index: 'Suivre la nutrition et corriger si besoin.',
  pressure: 'Observer les variations meteo.',
  heat: 'Conserver une temperature de confort plante.'
};

const SENSOR_THRESHOLDS = {
  luminosity: { min: 8000, max: 45000 },
  air_humidity: { min: 45, max: 75 },
  soil_humidity: { min: 30, max: 65 },
  co2: { min: 400, max: 1200 },
  nutrient_index: { min: 45, max: 90 },
  pressure: { min: 980, max: 1035 },
  heat: { min: 18, max: 29 }
};

const DEFAULT_SENSORS = [
  { type: 'luminosity', label: 'Luminosite', unit: 'lux' },
  { type: 'air_humidity', label: 'Humidite air', unit: '%' },
  { type: 'soil_humidity', label: 'Humidite sol', unit: '%' },
  { type: 'co2', label: 'CO2', unit: 'ppm' },
  { type: 'nutrient_index', label: 'Nutriments', unit: '%' },
  { type: 'pressure', label: 'Pression', unit: 'hpa' },
  { type: 'heat', label: 'Chaleur', unit: 'c' }
];

const SAMPLE_VALUES = {
  luminosity: 18500,
  air_humidity: 62,
  soil_humidity: 41.5,
  co2: 780,
  nutrient_index: 68,
  pressure: 1008,
  heat: 23.6
};

function escapeHtml(value) {
  const input = value == null ? '' : String(value);
  return input
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function normalizeSensors(rawSensors) {
  if (!Array.isArray(rawSensors)) return [];
  return rawSensors
    .map((sensor) => {
      if (!sensor || typeof sensor !== 'object') return null;
      const type = typeof sensor.type === 'string' ? sensor.type.trim() : '';
      if (!type) return null;

      const labelRaw = typeof sensor.label === 'string' ? sensor.label.trim() : '';
      const unit = typeof sensor.unit === 'string' ? sensor.unit.trim().toLowerCase() : '';

      return {
        type,
        label: labelRaw || SENSOR_LABELS_FR[type] || type,
        unit
      };
    })
    .filter(Boolean);
}

async function loadSensors() {
  try {
    const response = await fetch(`${API_BASE}/sensors`, {
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`Unexpected status: ${response.status}`);
    }
    const body = await response.json();
    const sensors = normalizeSensors(body && body.sensors);
    if (sensors.length > 0) return sensors;
  } catch (_error) {
    // Silent fallback for static frontend mode.
  }

  return DEFAULT_SENSORS;
}

function getSampleValue(sensorType, index) {
  if (Object.prototype.hasOwnProperty.call(SAMPLE_VALUES, sensorType)) {
    return SAMPLE_VALUES[sensorType];
  }
  return Number((10 + index * 3.2).toFixed(1));
}

function formatValue(value) {
  if (Number.isNaN(Number(value))) return '-';
  const n = Number(value);
  const decimals = Number.isInteger(n) ? 0 : 1;
  return n.toLocaleString('fr-FR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

function formatTimestamp(date) {
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getStateBadgeClass(level) {
  if (level === 'danger') return 'danger';
  if (level === 'warn') return 'warn';
  return '';
}

function getSensorState(sensorType, value) {
  const limits = SENSOR_THRESHOLDS[sensorType];
  if (!limits) return { level: 'ok', label: 'Stable' };

  if (value < limits.min || value > limits.max) {
    const reference = value < limits.min ? limits.min : limits.max;
    const distanceRatio = Math.abs(value - reference) / Math.max(Math.abs(reference), 1);
    if (distanceRatio >= 0.2) return { level: 'danger', label: 'Critique' };
    return { level: 'warn', label: 'Hors plage' };
  }

  const range = limits.max - limits.min;
  const nearestEdge = Math.min(value - limits.min, limits.max - value);
  if (range > 0 && nearestEdge / range < 0.12) {
    return { level: 'warn', label: 'Proche seuil' };
  }

  return { level: 'ok', label: 'Stable' };
}

function getTargetText(sensorType, unit) {
  const limits = SENSOR_THRESHOLDS[sensorType];
  if (!limits) return 'Plage cible non definie';
  return `Cible ${limits.min}-${limits.max} ${unit}`;
}

function buildSnapshot(sensors) {
  return sensors.map((sensor, index) => {
    const value = getSampleValue(sensor.type, index);
    return {
      sensor,
      value,
      state: getSensorState(sensor.type, value)
    };
  });
}

function ensureMetricCards(sensors) {
  const grid = document.getElementById('metrics-grid');
  if (!grid) return;

  grid.innerHTML = sensors
    .map(
      (sensor) => `
      <article class="metric-card" data-metric="${escapeHtml(sensor.type)}">
        <div class="metric-label">${escapeHtml(sensor.label)}</div>
        <div class="metric-value">-</div>
        <div class="metric-unit">${escapeHtml(sensor.unit)}</div>
        <div class="metric-note">${escapeHtml(SENSOR_HINTS[sensor.type] || '')}</div>
        <span class="badge">-</span>
      </article>
    `
    )
    .join('');
}

function updateMetrics(snapshot, measuredAt) {
  const byType = new Map(snapshot.map((item) => [item.sensor.type, item]));

  document.querySelectorAll('[data-metric]').forEach((card) => {
    const metricType = card.dataset.metric;
    const item = byType.get(metricType);
    if (!item) return;

    const valueEl = card.querySelector('.metric-value');
    const unitEl = card.querySelector('.metric-unit');
    const noteEl = card.querySelector('.metric-note');
    const badgeEl = card.querySelector('.badge');

    if (valueEl) valueEl.textContent = formatValue(item.value);
    if (unitEl) unitEl.textContent = item.sensor.unit;
    if (noteEl) noteEl.textContent = getTargetText(item.sensor.type, item.sensor.unit);
    if (badgeEl) {
      badgeEl.textContent = item.state.label;
      badgeEl.classList.remove('warn', 'danger');
      const badgeClass = getStateBadgeClass(item.state.level);
      if (badgeClass) badgeEl.classList.add(badgeClass);
    }
  });

  const lastUpdate = document.getElementById('last-update');
  if (lastUpdate) lastUpdate.textContent = formatTimestamp(measuredAt);
}

function populateReadings(snapshot, measuredAt) {
  const table = document.getElementById('readings-body');
  if (!table) return;

  table.innerHTML = snapshot
    .map((item) => {
      const badgeClass = getStateBadgeClass(item.state.level);
      return `
        <tr>
          <td>${escapeHtml(item.sensor.label)}</td>
          <td>${escapeHtml(formatValue(item.value))}</td>
          <td><span class="badge ${badgeClass}">${escapeHtml(item.state.label)}</span></td>
          <td>${escapeHtml(item.sensor.unit)}</td>
          <td>${escapeHtml(formatTimestamp(measuredAt))}</td>
        </tr>
      `;
    })
    .join('');
}

function populateSensorOptions(sensors) {
  const selectIds = ['sensor', 'alert-sensor'];

  selectIds.forEach((selectId) => {
    const select = document.getElementById(selectId);
    if (!select) return;

    const previousValue = select.value;
    const isAlertFilter = selectId === 'alert-sensor';

    const options = sensors.map(
      (sensor) =>
        `<option value="${escapeHtml(sensor.type)}">${escapeHtml(sensor.label)} (${escapeHtml(sensor.unit)})</option>`
    );

    if (isAlertFilter) {
      options.unshift('<option value="">Tous les capteurs</option>');
    }

    select.innerHTML = options.join('');

    if (previousValue && [...select.options].some((opt) => opt.value === previousValue)) {
      select.value = previousValue;
    }
  });
}

function buildAlerts(snapshot, measuredAt, mode) {
  const priority = { danger: 2, warn: 1, ok: 0 };

  const prioritized = [...snapshot].sort(
    (a, b) => priority[b.state.level] - priority[a.state.level]
  );

  const count = mode === 'history' ? Math.min(6, prioritized.length) : Math.min(3, prioritized.length);

  return prioritized.slice(0, count).map((item, idx) => {
    const fallbackLevel = idx === 0 ? 'warn' : 'ok';
    const level = item.state.level === 'ok' ? fallbackLevel : item.state.level;
    const time = new Date(measuredAt.getTime() - idx * 11 * 60 * 1000);
    return {
      level,
      title: `${item.sensor.label} - ${level === 'danger' ? 'intervention requise' : 'suivi conseille'}`,
      detail: `${formatValue(item.value)} ${item.sensor.unit} | ${SENSOR_HINTS[item.sensor.type] || ''}`,
      time: time.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    };
  });
}

function populateAlerts(snapshot, measuredAt) {
  const list = document.getElementById('alert-list');
  if (!list) return 0;

  const mode = list.dataset.mode === 'history' ? 'history' : 'latest';
  const alerts = buildAlerts(snapshot, measuredAt, mode);

  list.innerHTML = alerts
    .map((alert) => {
      const badgeClass = getStateBadgeClass(alert.level);
      return `
        <div class="alert-item ${badgeClass}">
          <div>
            <strong>${escapeHtml(alert.title)}</strong>
            <span>${escapeHtml(alert.detail)}</span>
          </div>
          <span class="badge ${badgeClass}">${escapeHtml(alert.time)}</span>
        </div>
      `;
    })
    .join('');

  return alerts.filter((alert) => alert.level !== 'ok').length;
}

function populateKpis(snapshot, measuredAt, alertCount) {
  const sensorsEl = document.getElementById('kpi-sensors');
  const alertsEl = document.getElementById('kpi-alerts');
  const syncEl = document.getElementById('kpi-sync');

  if (sensorsEl) sensorsEl.textContent = `${snapshot.length}`;
  if (alertsEl) alertsEl.textContent = `${alertCount}`;
  if (syncEl) {
    syncEl.textContent = measuredAt.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}

function populateInsights(snapshot) {
  const list = document.getElementById('insights-list');
  if (!list) return;

  const critical = snapshot.find((item) => item.state.level === 'danger');
  const warning = snapshot.find((item) => item.state.level === 'warn');
  const luminosity = snapshot.find((item) => item.sensor.type === 'luminosity');
  const co2 = snapshot.find((item) => item.sensor.type === 'co2');

  const lines = [
    luminosity
      ? `Luminosite: ${formatValue(luminosity.value)} ${luminosity.sensor.unit} (${luminosity.state.label}).`
      : 'Luminosite: information non disponible.',
    co2
      ? `CO2: ${formatValue(co2.value)} ${co2.sensor.unit} (${co2.state.label}).`
      : 'CO2: information non disponible.',
    warning
      ? `A surveiller: ${warning.sensor.label} proche de la limite.`
      : 'Aucune valeur proche de seuil detectee.',
    critical
      ? `Priorite: corriger ${critical.sensor.label} des que possible.`
      : 'Priorite: maintenir les reglages actuels.'
  ];

  list.innerHTML = lines.map((line) => `<li>${escapeHtml(line)}</li>`).join('');
}

function populateDeviceSensorState(snapshot) {
  const grid = document.getElementById('device-sensors-grid');
  if (!grid) return;

  grid.innerHTML = snapshot
    .map((item) => {
      const badgeClass = getStateBadgeClass(item.state.level);
      const hint = SENSOR_HINTS[item.sensor.type] || '';
      return `
        <article class="metric-card">
          <div class="metric-label">${escapeHtml(item.sensor.label)}</div>
          <div class="metric-value">${escapeHtml(formatValue(item.value))}</div>
          <div class="metric-unit">${escapeHtml(item.sensor.unit)}</div>
          <span class="badge ${badgeClass}">${escapeHtml(item.state.label)}</span>
          <div class="metric-note">${escapeHtml(hint)}</div>
        </article>
      `;
    })
    .join('');
}

document.addEventListener('DOMContentLoaded', async () => {
  const sensors = await loadSensors();
  const measuredAt = new Date();
  const snapshot = buildSnapshot(sensors);

  ensureMetricCards(sensors);
  updateMetrics(snapshot, measuredAt);
  populateReadings(snapshot, measuredAt);
  populateSensorOptions(sensors);

  const alertCount = populateAlerts(snapshot, measuredAt);
  populateKpis(snapshot, measuredAt, alertCount);
  populateInsights(snapshot);
  populateDeviceSensorState(snapshot);
});
