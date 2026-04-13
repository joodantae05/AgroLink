const API_BASE = window.AGROLINK_API_BASE || 'http://localhost:8000/api/v1';
const DEVICE_ID = window.AGROLINK_DEVICE_ID || '';

const IOT_SENSOR_TYPES = ['temperature', 'humidity_air', 'humidity_soil'];
const IOT_SENSOR_SET = new Set(IOT_SENSOR_TYPES);

const SENSOR_LABELS_FR = {
  temperature: 'Temperature',
  humidity_air: 'Humidite air',
  humidity_soil: 'Humidite sol'
};

const SENSOR_HINTS = {
  temperature: 'Conserver une temperature de confort pour la plante.',
  humidity_air: 'Eviter les extremes pour limiter le stress de la plante.',
  humidity_soil: 'Maintenir une humidite du substrat reguliere.'
};

const SENSOR_THRESHOLDS = {
  temperature: { min: 18, max: 30 },
  humidity_air: { min: 45, max: 80 },
  humidity_soil: { min: 35, max: 75 }
};

const DEFAULT_SENSORS = [
  { type: 'temperature', label: 'Temperature', unit: 'c' },
  { type: 'humidity_air', label: 'Humidite air', unit: '%' },
  { type: 'humidity_soil', label: 'Humidite sol', unit: '%' }
];

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
  const byType = new Map();

  rawSensors.forEach((sensor) => {
      if (!sensor || typeof sensor !== 'object') return null;
      const type = typeof sensor.type === 'string' ? sensor.type.trim() : '';
      if (!type || !IOT_SENSOR_SET.has(type)) return null;
      if (byType.has(type)) return null;

      const labelRaw = typeof sensor.label === 'string' ? sensor.label.trim() : '';
      const unit = typeof sensor.unit === 'string' ? sensor.unit.trim().toLowerCase() : '';

      byType.set(type, {
        type,
        label: labelRaw || SENSOR_LABELS_FR[type] || type,
        unit
      });
      return null;
    });

  return IOT_SENSOR_TYPES.map((type) => byType.get(type)).filter(Boolean);
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

function parseIsoDate(value) {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function normalizeSnapshotReadings(rawReadings) {
  if (!Array.isArray(rawReadings)) return new Map();

  const byType = new Map();
  rawReadings.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const type = typeof item.type === 'string' ? item.type.trim() : '';
    if (!type || !IOT_SENSOR_SET.has(type) || byType.has(type)) return;

    const numericValue = Number(item.value);
    if (!Number.isFinite(numericValue)) return;
    byType.set(type, numericValue);
  });

  return byType;
}

async function loadLatestSnapshot() {
  const params = new URLSearchParams();
  if (DEVICE_ID) params.set('device_id', DEVICE_ID);
  const query = params.toString();
  const url = `${API_BASE}/snapshot${query ? `?${query}` : ''}`;

  try {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) {
      throw new Error(`Unexpected status: ${response.status}`);
    }

    const body = await response.json();
    return {
      measuredAt: parseIsoDate(body && body.measured_at),
      valuesByType: normalizeSnapshotReadings(body && body.readings)
    };
  } catch (_error) {
    return { measuredAt: null, valuesByType: new Map() };
  }
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') return '-';
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
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
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return { level: 'ok', label: 'Sans mesure' };

  const limits = SENSOR_THRESHOLDS[sensorType];
  if (!limits) return { level: 'ok', label: 'Stable' };

  if (numericValue < limits.min || numericValue > limits.max) {
    const reference = numericValue < limits.min ? limits.min : limits.max;
    const distanceRatio = Math.abs(numericValue - reference) / Math.max(Math.abs(reference), 1);
    if (distanceRatio >= 0.2) return { level: 'danger', label: 'Critique' };
    return { level: 'warn', label: 'Hors plage' };
  }

  const range = limits.max - limits.min;
  const nearestEdge = Math.min(numericValue - limits.min, limits.max - numericValue);
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

function buildSnapshot(sensors, valuesByType) {
  return sensors.map((sensor) => {
    const liveValue = valuesByType && valuesByType.has(sensor.type) ? valuesByType.get(sensor.type) : null;
    const value = Number.isFinite(liveValue) ? liveValue : null;
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
  const validSnapshot = snapshot.filter(
    (item) => item.value !== null && item.value !== undefined && Number.isFinite(Number(item.value))
  );

  const prioritized = [...validSnapshot].sort(
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

  if (alerts.length === 0) {
    list.innerHTML =
      '<div class="alert-item"><div><strong>Aucune alerte</strong><span>En attente de donnees capteurs depuis la base.</span></div><span class="badge">--:--</span></div>';
    return 0;
  }

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
  const caution = snapshot.find((item) => item.state.level === 'warn');
  const temperature = snapshot.find((item) => item.sensor.type === 'temperature');
  const humidityAir = snapshot.find((item) => item.sensor.type === 'humidity_air');
  const humiditySoil = snapshot.find((item) => item.sensor.type === 'humidity_soil');

  const lines = [
    temperature
      ? `Temperature: ${formatValue(temperature.value)} ${temperature.sensor.unit} (${temperature.state.label}).`
      : 'Temperature: information non disponible.',
    humidityAir
      ? `Humidite air: ${formatValue(humidityAir.value)} ${humidityAir.sensor.unit} (${humidityAir.state.label}).`
      : 'Humidite air: information non disponible.',
    humiditySoil
      ? `Humidite sol: ${formatValue(humiditySoil.value)} ${humiditySoil.sensor.unit} (${humiditySoil.state.label}).`
      : 'Humidite sol: information non disponible.',
    critical
      ? `Priorite: corriger ${critical.sensor.label} des que possible.`
      : caution
        ? `A surveiller: ${caution.sensor.label} proche de la limite.`
        : 'Aucune alerte capteur detectee.'
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
  const liveSnapshot = await loadLatestSnapshot();
  const measuredAt = liveSnapshot.measuredAt || new Date();
  const snapshot = buildSnapshot(sensors, liveSnapshot.valuesByType);

  ensureMetricCards(sensors);
  updateMetrics(snapshot, measuredAt);
  populateReadings(snapshot, measuredAt);
  populateSensorOptions(sensors);

  const alertCount = populateAlerts(snapshot, measuredAt);
  populateKpis(snapshot, measuredAt, alertCount);
  populateInsights(snapshot);
  populateDeviceSensorState(snapshot);
});
