import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// ─── Static placeholder data (replaced by live fetch below) ──────────────────

const PLACEHOLDER = {
  location: { city: 'New York', region: 'New York', country: 'US' },
  current: {
    temperature_c: 18, feels_like_c: 16, temp_min_c: 11, temp_max_c: 20,
    humidity_pct: 62, pressure_hpa: 1013, wind_speed_ms: 4.1, wind_deg: 270,
    cloud_cover_pct: 45, visibility_m: 10000, rain_1h_mm: 0, condition_id: 802,
    description: 'Scattered Clouds', icon: '03d',
    sunrise: 1700040000, sunset: 1700077200, dt: Date.now() / 1000,
  },
  hourly: Array.from({ length: 16 }, (_, i) => ({
    dt: Date.now() / 1000 + i * 10800,
    datetime: new Date(Date.now() + i * 10800000).toISOString(),
    temperature_c: 18 - Math.sin(i * 0.4) * 4,
    feels_like_c: 16 - Math.sin(i * 0.4) * 4,
    humidity_pct: 60 + i * 1.2,
    wind_speed_ms: 3 + Math.random() * 3,
    cloud_cover_pct: 40 + i * 2,
    description: ['Partly Cloudy', 'Scattered Clouds', 'Clear', 'Overcast'][i % 4],
    icon: ['02d', '03d', '01d', '04d'][i % 4],
    condition_id: [801, 802, 800, 804][i % 4],
    pop: Math.random() * 0.3,
    rain_3h_mm: 0,
  })),
  daily: [
    { date: 'Today',  icon: '03d', condition_id: 802, temp_min_c: 11, temp_max_c: 20, description: 'Partly Cloudy', pop: 0.1, rain_mm: 0,  humidity_pct: 62, wind_speed_max_ms: 5 },
    { date: 'Wed',    icon: '10d', condition_id: 501, temp_min_c: 9,  temp_max_c: 15, description: 'Rain',          pop: 0.8, rain_mm: 8,  humidity_pct: 80, wind_speed_max_ms: 7 },
    { date: 'Thu',    icon: '11d', condition_id: 211, temp_min_c: 8,  temp_max_c: 13, description: 'Thunderstorm',  pop: 0.9, rain_mm: 12, humidity_pct: 88, wind_speed_max_ms: 11 },
    { date: 'Fri',    icon: '01d', condition_id: 800, temp_min_c: 12, temp_max_c: 22, description: 'Sunny',         pop: 0.0, rain_mm: 0,  humidity_pct: 45, wind_speed_max_ms: 3 },
    { date: 'Sat',    icon: '02d', condition_id: 801, temp_min_c: 14, temp_max_c: 24, description: 'Mostly Clear',  pop: 0.05,rain_mm: 0,  humidity_pct: 48, wind_speed_max_ms: 4 },
    { date: 'Sun',    icon: '03d', condition_id: 802, temp_min_c: 13, temp_max_c: 21, description: 'Cloudy',        pop: 0.15,rain_mm: 1,  humidity_pct: 58, wind_speed_max_ms: 5 },
    { date: 'Mon',    icon: '10d', condition_id: 500, temp_min_c: 10, temp_max_c: 17, description: 'Light Rain',    pop: 0.6, rain_mm: 4,  humidity_pct: 75, wind_speed_max_ms: 6 },
  ],
  air_quality: { aqi: 1, aqi_label: 'Good', pm2_5: 4.2, pm10: 8.1, o3: 62, no2: 18 },
  ai: {
    summary: 'A comfortable afternoon in New York with scattered clouds and a light westerly breeze. Great conditions for being outside — a light jacket is all you\'ll need.',
    recommendations: ['Wear a light jacket', 'Good day for outdoor activities', 'No rain expected today'],
    alert: null,
  },
  overlay: { theme: { mode: 'light' } },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const OWM_ICONS = {
  '01d': '☀️', '01n': '🌙',
  '02d': '🌤', '02n': '🌤',
  '03d': '⛅', '03n': '⛅',
  '04d': '☁️', '04n': '☁️',
  '09d': '🌧', '09n': '🌧',
  '10d': '🌦', '10n': '🌦',
  '11d': '⛈',  '11n': '⛈',
  '13d': '❄️', '13n': '❄️',
  '50d': '🌫', '50n': '🌫',
};
const icon = (code) => OWM_ICONS[code] ?? '🌡';

function windDir(deg) {
  const dirs = ['N','NE','E','SE','S','SW','W','NW'];
  return dirs[Math.round(deg / 45) % 8];
}

function fmtHour(isoStr) {
  const d = new Date(isoStr);
  const h = d.getHours();
  if (h === 0) return '12AM';
  if (h === 12) return '12PM';
  return h > 12 ? `${h - 12}PM` : `${h}AM`;
}

function bgGradient(hour, condId) {
  if (hour < 6 || hour >= 21)  return 'from-[#0f2027] via-[#203a43] to-[#2c5364]';
  if (hour < 9)                return 'from-[#fda085] via-[#f6d365] to-[#87ceeb]';
  if (hour < 17)               return 'from-[#42a5f5] via-[#64b5f6] to-[#90caf9]';
  if (hour < 20)               return 'from-[#ff8c42] via-[#ffd580] to-[#c94b4b]';
  return 'from-[#1a1a2e] via-[#16213e] to-[#0f3460]';
}

const AQI_COLOR = { 1: '#34d399', 2: '#fbbf24', 3: '#fb923c', 4: '#f87171', 5: '#c084fc' };
const AQI_LABEL = { 1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor' };

// ─── Glass CSS (inline, Tailwind JIT may not flush all arbitrary values) ──────

const glass = {
  backdropFilter: 'blur(20px) saturate(180%)',
  WebkitBackdropFilter: 'blur(20px) saturate(180%)',
  background: 'rgba(255,255,255,0.13)',
  border: '1px solid rgba(255,255,255,0.25)',
  borderRadius: 18,
  boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
};
const glassDark = {
  ...glass,
  background: 'rgba(10,20,40,0.30)',
  border: '1px solid rgba(255,255,255,0.10)',
};

// ─── Tab icons ────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'today',    label: 'Today',    svg: 'M12 3a9 9 0 110 18A9 9 0 0112 3zm0 2a7 7 0 100 14A7 7 0 0012 5zm0 2a5 5 0 110 10A5 5 0 0112 7z' },
  { id: 'hourly',   label: 'Hourly',   svg: 'M12 2a10 10 0 110 20A10 10 0 0112 2zm0 2a8 8 0 100 16A8 8 0 0012 4zm1 4v5.586l3.707 3.707-1.414 1.414L11 14.414V8h2z' },
  { id: 'forecast', label: 'Forecast', svg: 'M3 5h18v2H3V5zm0 6h18v2H3v-2zm0 6h18v2H3v-2z' },
  { id: 'radar',    label: 'Radar',    svg: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93V18c0-.55.45-1 1-1s1 .45 1 1v1.93A8.001 8.001 0 014.07 13H6c.55 0 1 .45 1 1s-.45 1-1 1H4.07C4.56 17.19 8.03 20 12 20zm0-4c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm5.93 1H16c-.55 0-1-.45-1-1s.45-1 1-1h1.93A8.001 8.001 0 0013 4.07V6c0 .55-.45 1-1 1s-1-.45-1-1V4.07A8.001 8.001 0 004.07 11H6c.55 0 1 .45 1 1s-.45 1-1 1H4.07' },
  { id: 'ai',       label: 'AI Chat',  svg: 'M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z' },
];

// ─── Radar layer updater ──────────────────────────────────────────────────────

function RadarLayer({ apiKey }) {
  const map = useMap();
  useEffect(() => { map.invalidateSize(); }, [map]);
  return (
    <TileLayer
      url={`https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${apiKey}`}
      opacity={0.6}
      attribution="© OpenWeatherMap"
    />
  );
}

// ─── Views ────────────────────────────────────────────────────────────────────

function TodayView({ data, dark }) {
  const c = data.current;
  const ai = data.ai;
  const aqi = data.air_quality;
  const loc = data.location;

  return (
    <div className="flex flex-col gap-3 pb-4">
      {/* Hero */}
      <div className="text-center py-2">
        <p style={{ fontSize: 96, lineHeight: 1, fontWeight: 100, color: '#fff' }}>
          {Math.round(c.temperature_c)}°
        </p>
        <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: 20, marginTop: 6 }}>
          {c.description.replace(/\b\w/g, l => l.toUpperCase())}
        </p>
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 14, marginTop: 4 }}>
          H:{Math.round(c.temp_max_c)}° · L:{Math.round(c.temp_min_c)}° · Feels {Math.round(c.feels_like_c)}°
        </p>
      </div>

      {/* AI Summary */}
      {ai?.summary && (
        <div style={glass} className="p-4">
          <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>AI Summary</p>
          <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: 14, lineHeight: 1.6 }}>{ai.summary}</p>
        </div>
      )}

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
        {[
          { label: 'Humidity',  value: `${c.humidity_pct}%`,                    icon: '💧' },
          { label: 'Wind',      value: `${c.wind_speed_ms} m/s ${windDir(c.wind_deg ?? 0)}`, icon: '💨' },
          { label: 'Pressure',  value: `${c.pressure_hpa} hPa`,                 icon: '🌡' },
          { label: 'Visibility',value: c.visibility_m ? `${(c.visibility_m/1000).toFixed(1)} km` : '—', icon: '👁' },
          { label: 'Cloud',     value: `${c.cloud_cover_pct}%`,                 icon: '☁️' },
          { label: 'Rain',      value: `${c.rain_1h_mm ?? 0} mm`,               icon: '🌧' },
        ].map(({ label, value, icon: i }) => (
          <div key={label} style={glass} className="p-3 text-center">
            <div style={{ fontSize: 20 }}>{i}</div>
            <div style={{ color: '#fff', fontSize: 13, fontWeight: 600, marginTop: 4 }}>{value}</div>
            <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* AQI */}
      {aqi?.aqi && (
        <div style={glass} className="px-4 py-3 flex items-center justify-between">
          <div>
            <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Air Quality</p>
            <p style={{ color: AQI_COLOR[aqi.aqi] || '#fff', fontSize: 15, fontWeight: 700, marginTop: 2 }}>
              {AQI_LABEL[aqi.aqi]} · AQI {aqi.aqi}
            </p>
          </div>
          <div style={{ textAlign: 'right', fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>
            {aqi.pm2_5 != null && <div>PM2.5 · {aqi.pm2_5.toFixed(1)}</div>}
            {aqi.pm10  != null && <div>PM10  · {aqi.pm10.toFixed(1)}</div>}
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {ai?.recommendations?.length > 0 && (
        <div style={glass} className="p-4">
          <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>Recommendations</p>
          {ai.recommendations.map((r, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 6 }}>
              <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14, marginTop: 1 }}>›</span>
              <p style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14, lineHeight: 1.5 }}>{r}</p>
            </div>
          ))}
        </div>
      )}

      {/* Severe alert */}
      {ai?.alert && (
        <div style={{ ...glass, background: 'rgba(239,68,68,0.25)', border: '1px solid rgba(239,68,68,0.4)' }} className="p-4 flex gap-3 items-start">
          <span style={{ fontSize: 20 }}>⚠️</span>
          <p style={{ color: '#fca5a5', fontSize: 14, lineHeight: 1.5 }}>{ai.alert}</p>
        </div>
      )}
    </div>
  );
}

function HourlyView({ data }) {
  const entries = data.hourly ?? [];

  return (
    <div className="flex flex-col gap-3 pb-4">
      <div style={glass} className="p-4">
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12 }}>
          48-Hour Forecast
        </p>

        {/* Horizontal scroll row */}
        <div style={{ display: 'flex', gap: 16, overflowX: 'auto', paddingBottom: 8, scrollbarWidth: 'none' }}>
          {entries.map((e, i) => {
            const isNow = i === 0;
            return (
              <div key={e.dt} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 52, gap: 5 }}>
                <p style={{ color: isNow ? '#fff' : 'rgba(255,255,255,0.55)', fontSize: 12, fontWeight: isNow ? 700 : 400 }}>
                  {isNow ? 'Now' : fmtHour(e.datetime)}
                </p>
                <span style={{ fontSize: 22 }}>{icon(e.icon)}</span>
                {e.pop > 0.05 && (
                  <p style={{ color: '#7dd3fc', fontSize: 10 }}>{Math.round(e.pop * 100)}%</p>
                )}
                <p style={{ color: '#fff', fontSize: 14, fontWeight: 500 }}>{Math.round(e.temperature_c)}°</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Hourly detail table */}
      <div style={glass} className="p-4">
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10 }}>
          Details
        </p>
        {entries.slice(0, 12).map((e, i) => (
          <div key={e.dt} style={{
            display: 'grid', gridTemplateColumns: '56px 32px 44px 1fr 44px 44px',
            alignItems: 'center', gap: 8, padding: '7px 0',
            borderBottom: i < 11 ? '1px solid rgba(255,255,255,0.07)' : 'none',
          }}>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>{i === 0 ? 'Now' : fmtHour(e.datetime)}</p>
            <span style={{ fontSize: 18, textAlign: 'center' }}>{icon(e.icon)}</span>
            <p style={{ color: '#fff', fontSize: 14, fontWeight: 600 }}>{Math.round(e.temperature_c)}°</p>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12 }}>{e.description}</p>
            <p style={{ color: '#7dd3fc', fontSize: 12, textAlign: 'right' }}>
              {e.pop > 0.05 ? `${Math.round(e.pop * 100)}%` : '—'}
            </p>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, textAlign: 'right' }}>
              {e.wind_speed_ms?.toFixed(1)} m/s
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ForecastView({ data }) {
  const [expanded, setExpanded] = useState(null);
  const days = data.daily ?? [];

  return (
    <div className="flex flex-col gap-3 pb-4">
      <div style={glass} className="p-4">
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12 }}>
          7-Day Forecast
        </p>
        {days.map((d, i) => {
          const open = expanded === i;
          return (
            <div key={d.date}>
              <div
                onClick={() => setExpanded(open ? null : i)}
                style={{
                  display: 'grid', gridTemplateColumns: '64px 28px 1fr 36px 36px 20px',
                  alignItems: 'center', gap: 8, padding: '10px 0', cursor: 'pointer',
                  borderBottom: !open && i < days.length - 1 ? '1px solid rgba(255,255,255,0.07)' : 'none',
                }}
              >
                <p style={{ color: '#fff', fontSize: 14, fontWeight: 500 }}>{d.date}</p>
                <span style={{ fontSize: 20 }}>{icon(d.icon)}</span>
                <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 12 }}>{d.description}</p>
                <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 13, textAlign: 'right' }}>
                  {Math.round(d.temp_min_c)}°
                </p>
                <p style={{ color: '#fff', fontSize: 13, fontWeight: 600, textAlign: 'right' }}>
                  {Math.round(d.temp_max_c)}°
                </p>
                <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, textAlign: 'right' }}>{open ? '▲' : '▼'}</p>
              </div>

              {open && (
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
                  gap: 8, padding: '10px 0 14px',
                  borderBottom: i < days.length - 1 ? '1px solid rgba(255,255,255,0.07)' : 'none',
                }}>
                  {[
                    { label: 'Humidity',  value: `${Math.round(d.humidity_pct)}%` },
                    { label: 'Wind',      value: `${d.wind_speed_max_ms?.toFixed(1)} m/s` },
                    { label: 'Rain',      value: `${d.rain_mm?.toFixed(1)} mm` },
                    { label: 'Precip %',  value: `${Math.round((d.pop ?? 0) * 100)}%` },
                    { label: 'Feels Min', value: `${Math.round(d.feels_like_min_c ?? d.temp_min_c)}°` },
                    { label: 'Feels Max', value: `${Math.round(d.feels_like_max_c ?? d.temp_max_c)}°` },
                  ].map(({ label, value }) => (
                    <div key={label} style={{
                      background: 'rgba(255,255,255,0.08)', borderRadius: 10, padding: '8px 10px',
                    }}>
                      <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 11 }}>{label}</p>
                      <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, marginTop: 2 }}>{value}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RadarView({ data, apiKey }) {
  const loc = data.location;
  const center = [loc?.lat ?? 40.71, loc?.lon ?? -74.01];

  return (
    <div className="flex flex-col gap-3 pb-4">
      <div style={{ ...glass, overflow: 'hidden', height: 360 }}>
        <MapContainer
          center={center}
          zoom={7}
          style={{ height: '100%', width: '100%', background: 'transparent' }}
          zoomControl={true}
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution="© CartoDB"
          />
          {apiKey && <RadarLayer apiKey={apiKey} />}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
            attribution=""
          />
        </MapContainer>
      </div>

      {/* Legend */}
      <div style={glass} className="p-4">
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10 }}>
          Precipitation Radar
        </p>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {['#7ec8e3','#3a86ff','#00b4d8','#0077b6','#023e8a'].map((c, i) => (
            <div key={i} style={{ flex: 1, height: 8, background: c, borderRadius: 4 }} />
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
          <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 10 }}>Light</p>
          <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 10 }}>Heavy</p>
        </div>
        <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11, marginTop: 8 }}>
          Data: OpenWeatherMap · Updated every 10 min
        </p>
      </div>
    </div>
  );
}

const AI_CHIPS = [
  'Should I bring an umbrella?',
  'What should I wear today?',
  'Good day for a run?',
  'Is it safe to drive?',
  'Best time to go outside?',
  'Any severe weather?',
];

function AiView({ data }) {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: data.ai?.summary ?? 'Hello! Ask me anything about today\'s weather.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const c = data.current;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    if (!text.trim() || loading) return;
    const q = text.trim();
    setInput('');
    setMessages(m => [...m, { role: 'user', text: q }]);
    setLoading(true);

    try {
      const res = await fetch(
        `/api/weather?lat=${data.location?.lat ?? 40.71}&lon=${data.location?.lon ?? -74.01}&ai=true`
      );
      const json = await res.json();
      const ai = json.ai ?? {};

      let answer = '';
      const ql = q.toLowerCase();

      if (ql.includes('umbrella') || ql.includes('rain')) {
        const rain = c.rain_1h_mm > 0 || (c.condition_id >= 300 && c.condition_id < 600);
        answer = rain
          ? `Yes — ${c.description} with ${c.rain_1h_mm ?? 0} mm in the last hour. Definitely bring an umbrella.`
          : `No rain right now. ${ai.summary ?? 'Enjoy the dry weather!'}`;
      } else if (ql.includes('wear') || ql.includes('outfit') || ql.includes('clothes')) {
        answer = ai.recommendations?.join('. ') ?? _localRec(c);
      } else if (ql.includes('run') || ql.includes('exercise') || ql.includes('outside')) {
        const ok = c.temperature_c > 5 && c.temperature_c < 32 && c.wind_speed_ms < 12 && !c.rain_1h_mm;
        answer = ok
          ? `Good conditions for outdoor activity — ${Math.round(c.temperature_c)}°C, ${c.wind_speed_ms} m/s wind.`
          : `Conditions are ${c.description.toLowerCase()} at ${Math.round(c.temperature_c)}°C. ${ok ? 'Go for it!' : 'You may want to wait.'}`;
      } else if (ql.includes('drive') || ql.includes('road')) {
        const bad = c.visibility_m < 500 || c.wind_speed_ms > 15 || (c.condition_id >= 200 && c.condition_id < 300);
        answer = bad
          ? `⚠️ Exercise caution — visibility ${c.visibility_m ?? '?'} m, winds ${c.wind_speed_ms} m/s.`
          : `Driving conditions look fine. Visibility is good at ${(c.visibility_m / 1000).toFixed(1)} km.`;
      } else if (ql.includes('severe') || ql.includes('alert') || ql.includes('warning')) {
        answer = ai.alert ?? 'No severe weather alerts at this time.';
      } else if (ql.includes('best time')) {
        answer = `Best time to go outside is around midday when temps peak at ${Math.round(c.temp_max_c ?? c.temperature_c)}°C. ${ai.summary ?? ''}`;
      } else {
        answer = ai.summary ?? `Currently ${Math.round(c.temperature_c)}°C with ${c.description.toLowerCase()}.`;
      }

      setMessages(m => [...m, { role: 'ai', text: answer }]);
    } catch {
      setMessages(m => [...m, { role: 'ai', text: `Currently ${Math.round(c.temperature_c)}°C with ${c.description.toLowerCase()}. Ask me anything else!` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 10 }}>
      {/* Chat window */}
      <div style={{ ...glass, flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0, maxHeight: 380, scrollbarWidth: 'none' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%', padding: '10px 14px', borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              background: m.role === 'user' ? 'rgba(59,130,246,0.55)' : 'rgba(255,255,255,0.15)',
              border: '1px solid rgba(255,255,255,0.15)',
              color: '#fff', fontSize: 14, lineHeight: 1.5,
            }}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '10px 16px', background: 'rgba(255,255,255,0.15)', borderRadius: '18px 18px 18px 4px', color: 'rgba(255,255,255,0.6)', fontSize: 20 }}>
              ···
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick chips */}
      <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4, scrollbarWidth: 'none' }}>
        {AI_CHIPS.map(chip => (
          <button
            key={chip}
            onClick={() => send(chip)}
            style={{
              whiteSpace: 'nowrap', padding: '6px 14px',
              background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.22)',
              borderRadius: 20, color: 'rgba(255,255,255,0.85)', fontSize: 12, cursor: 'pointer',
            }}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send(input)}
          placeholder="Ask about the weather…"
          style={{
            flex: 1, padding: '12px 16px',
            background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.22)',
            borderRadius: 24, color: '#fff', fontSize: 14, outline: 'none',
          }}
        />
        <button
          onClick={() => send(input)}
          disabled={loading || !input.trim()}
          style={{
            width: 44, height: 44, borderRadius: '50%',
            background: input.trim() ? 'rgba(59,130,246,0.7)' : 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            color: '#fff', fontSize: 18, cursor: 'pointer', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          ↑
        </button>
      </div>
    </div>
  );
}

function _localRec(c) {
  const t = c.temperature_c;
  if (t < 0) return 'Heavy coat, hat, gloves, and waterproof boots.';
  if (t < 10) return 'Warm jacket, layers, and a scarf.';
  if (t < 18) return 'A light to medium jacket should be fine.';
  if (t < 25) return 'Light clothing — a cardigan or light jacket for evenings.';
  return 'Light, breathable clothing. Stay hydrated!';
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [tab, setTab] = useState('today');
  const [data, setData] = useState(PLACEHOLDER);
  const [time, setTime] = useState(new Date());
  const API_KEY = process.env.REACT_APP_OPENWEATHER_API_KEY ?? '';

  // Live clock
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 60000);
    return () => clearInterval(t);
  }, []);

  // Fetch weather from backend
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/weather?ai=true');
        if (res.ok) {
          const json = await res.json();
          if (json?.current) setData(json);
        }
      } catch { /* keep placeholder */ }
    })();
  }, []);

  const hour = time.getHours();
  const bg = bgGradient(hour, data.current?.condition_id);
  const loc = data.location ?? {};

  const VIEWS = {
    today:    <TodayView data={data} />,
    hourly:   <HourlyView data={data} />,
    forecast: <ForecastView data={data} />,
    radar:    <RadarView data={data} apiKey={API_KEY} />,
    ai:       <AiView data={data} />,
  };

  return (
    <div
      style={{ position: 'relative', height: '100vh', width: '100vw', overflow: 'hidden' }}
      className={`bg-gradient-to-br ${bg}`}
    >
      {/* Ambient orbs */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: -80, left: -80, width: 320, height: 320, borderRadius: '50%', background: 'rgba(255,255,255,0.08)', filter: 'blur(60px)' }} />
        <div style={{ position: 'absolute', bottom: -60, right: -60, width: 280, height: 280, borderRadius: '50%', background: 'rgba(255,255,255,0.06)', filter: 'blur(50px)' }} />
      </div>

      {/* Layout */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', height: '100%', maxWidth: 440, margin: '0 auto', padding: '0 18px' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', paddingTop: 48, paddingBottom: 4, flexShrink: 0 }}>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
          <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 600, marginTop: 4 }}>
            {loc.city ?? 'Loading…'}
          </h1>
          {loc.region && (
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>{loc.region}, {loc.country}</p>
          )}
        </div>

        {/* Scrollable content */}
        <div style={{ flex: 1, overflowY: 'auto', paddingTop: 12, paddingBottom: 8, scrollbarWidth: 'none' }}>
          {VIEWS[tab]}
        </div>

        {/* Tab bar */}
        <div style={{ ...glass, flexShrink: 0, display: 'flex', justifyContent: 'space-around', padding: '10px 6px 14px', marginBottom: 8 }}>
          {TABS.map(({ id, label, svg }) => {
            const active = tab === id;
            return (
              <button
                key={id}
                onClick={() => setTab(id)}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                  background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px',
                  opacity: active ? 1 : 0.45, transition: 'opacity 0.2s',
                }}
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#fff' : 'rgba(255,255,255,0.7)'}>
                  <path d={svg} />
                </svg>
                <span style={{ color: active ? '#fff' : 'rgba(255,255,255,0.6)', fontSize: 10, fontWeight: active ? 600 : 400 }}>
                  {label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
