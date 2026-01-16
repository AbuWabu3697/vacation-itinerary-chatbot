// ---------------- Travel Interests ----------------
let selectedInterests = [];

// Option button toggle
document.querySelectorAll('.option-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    this.classList.toggle('active');
    const interest = this.textContent.trim();
    
    if (this.classList.contains('active')) {
      selectedInterests.push(interest);
    } else {
      selectedInterests = selectedInterests.filter(i => i !== interest);
    }
  });
});

// ---------------- Send Button ----------------
document.getElementById('sendBtn').addEventListener('click', handleSendMessage);
document.getElementById('userInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') handleSendMessage();
});

function handleSendMessage() {
  const userInput = document.getElementById('userInput');
  const destination = document.getElementById('destination').value;
  const dates = document.getElementById('dates').value;
  const budget = document.getElementById('budget').value;
  const transport = document.getElementById('transport').value;
  const message = userInput.value.trim();

  if (!message) return;

  if (!destination || !dates || !budget) {
    alert('Please fill in destination, dates, and budget to continue.');
    return;
  }

  displayMessage(message, 'user');
  userInput.value = '';

  const botResponse = generateItinerary(destination, dates, budget, transport, selectedInterests, message);
  setTimeout(() => displayMessage(botResponse, 'bot'), 500);
  searchFlights();
  setTimeout(() => displayMessage(botResponse, 'bot'), 500);
}

function displayMessage(text, sender) {
  const chatBox = document.getElementById('chatBox');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  if (sender === 'bot') {
    messageDiv.innerHTML = `<p>${text}</p>`;
  } else {
    messageDiv.innerHTML = `<p style="background: #2563eb; color: white; margin-left: auto; max-width: 85%;">${text}</p>`;
  }
  
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function mdYToISO(mdY) {
  // "2/1/2026" -> "2026-02-01"
  const parts = mdY.trim().split("/");
  if (parts.length !== 3) return null;

  const [m, d, y] = parts.map(p => p.trim());
  if (!m || !d || !y) return null;

  const mm = String(parseInt(m, 10)).padStart(2, "0");
  const dd = String(parseInt(d, 10)).padStart(2, "0");
  return `${y}-${mm}-${dd}`;
}

function normalizeDatesForBackend(datesStr) {
  // if it's already ISO, leave it
  if (/\d{4}-\d{2}-\d{2}/.test(datesStr)) return datesStr;

  // expected "M/D/YYYY - M/D/YYYY"
  const parts = datesStr.split("-").map(s => s.trim());
  if (parts.length < 2) return datesStr;

  const startISO = mdYToISO(parts[0]);
  const endISO = mdYToISO(parts[1]);

  if (!startISO || !endISO) return datesStr;

  return `${startISO} to ${endISO}`;
}

function parseBudgetMax(budgetValue) {
  // "2000-4000" -> "4000"
  if (!budgetValue) return "";
  if (budgetValue.includes("+")) return ""; // treat "No Budget" as no max

  const parts = budgetValue.split("-").map(s => s.trim());
  if (parts.length === 2 && parts[1]) return parts[1];

  // if it's already a number
  return budgetValue;
}

const userInput = document.getElementById('userInput');
async function searchFlights() {
  const destination = document.getElementById('destination').value.trim();
  const datesRaw = document.getElementById('dates').value.trim();
  const dates = normalizeDatesForBackend(datesRaw);

  const budgetRaw = document.getElementById('budget').value.trim();
  const budget = parseBudgetMax(budgetRaw);
  const transport = document.getElementById('transport').value.trim();
  const message = userInput.value.trim();

  const origin = "BOS";

  const payload = {
    origin,
    destination,
    dates,
    budget,
    transport,
    message
  };

  const res = await fetch("/api/flights", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  console.log("flight results:", data);

  // 🔥 ADD THIS BLOCK RIGHT HERE
  if (data.error) {
    const msg = data.message ? ` (${data.message})` : "";
    displayMessage("❌ " + data.error + msg, "bot");
    return;
  }

  // ✅ If no error, continue rendering flights
  displayMessage("✈️ Found " + data.offers.length + " flights!", "bot");

  // TODO: format flight cards here
}



function generateItinerary(destination, dates, budget, transport, interests, userMessage) {
  return `Great! I'm planning a trip to ${destination} from ${dates} with a ${budget} budget. 
  Transportation: ${transport}. Your interests: ${interests.length > 0 ? interests.join(', ') : 'general sightseeing'}. 
  Special requests: ${userMessage}. Your personalized itinerary is being generated...`;
}

// ---------------- Tabs JS ----------------
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(b => b.classList.remove('active'));
    tabContents.forEach(tc => tc.classList.remove('active'));

    btn.classList.add('active');
    const tabId = btn.dataset.tab;
    document.getElementById(`${tabId}-tab`).classList.add('active');
  });
});

// ---------------- Explore Destinations Grid ----------------
const exploreGrid = document.querySelector('.explore-placeholder') || document.getElementById('cityGrid');

const cities = [
  "Paris","Tokyo","New York","London","Barcelona","Rome","Amsterdam","Berlin","Sydney","Dubai",
  "Bangkok","Singapore","Istanbul","Prague","Vienna","Hong Kong","Lisbon","Seoul","Los Angeles","Chicago",
  "Rio de Janeiro","Cape Town","Vancouver","Mexico City","Buenos Aires","Moscow","Athens","Cairo","Budapest","Miami"
];

cities.forEach(city => {
  const btn = document.createElement('button');
  btn.textContent = city;

  btn.addEventListener('click', () => {
    document.getElementById('destination').value = city;
    // NOTE: do NOT switch tabs here anymore
  });

  exploreGrid.appendChild(btn);
});

// ---------------- Calendar Popup ----------------
function initDatePicker() {
  const datesInput = document.getElementById('dates');
  datesInput.addEventListener('click', openStartCalendar);
}

function openStartCalendar() {
  openCalendar('start');
}

function openEndCalendar() {
  openCalendar('end');
}

function openCalendar(mode) {
  const overlay = document.createElement('div');
  overlay.className = 'calendar-overlay';
  
  const calendarPopup = document.createElement('div');
  calendarPopup.className = 'calendar-popup';
  
  const today = new Date();
  let currentMonth = today.getMonth();
  let currentYear = today.getFullYear();
  
  calendarPopup.innerHTML = generateCalendarHTML(currentMonth, currentYear);
  overlay.appendChild(calendarPopup);
  document.body.appendChild(overlay);

  function refreshCalendar(month, year) {
    calendarPopup.innerHTML = generateCalendarHTML(month, year);
    attachDayListeners();
    attachNavListeners();
  }

  function attachNavListeners() {
    document.querySelectorAll('.calendar-nav-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        let newMonth = currentMonth + (this.dataset.direction === 'next' ? 1 : -1);
        let newYear = currentYear;

        if (newMonth > 11) { newMonth = 0; newYear++; }
        if (newMonth < 0) { newMonth = 11; newYear--; }

        currentMonth = newMonth;
        currentYear = newYear;
        refreshCalendar(currentMonth, currentYear);
      });
    });
  }

  function attachDayListeners() {
    document.querySelectorAll('.calendar-day').forEach(day => {
      day.addEventListener('click', function() {
        if (!this.textContent) return;
        const selectedDate = `${currentMonth + 1}/${this.textContent}/${currentYear}`;
        const datesInput = document.getElementById('dates');

        if (mode === 'start') {
          datesInput.value = selectedDate;
          overlay.remove();
          setTimeout(() => openEndCalendar(), 200);
        } else if (mode === 'end') {
          const startDate = datesInput.value;
          datesInput.value = `${startDate} - ${selectedDate}`;
          overlay.remove();
        }
      });
    });
  }

  attachNavListeners();
  attachDayListeners();

  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) overlay.remove();
  });
}

function generateCalendarHTML(month, year) {
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  let html = `<div style="padding:1.5rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
      <button class="calendar-nav-btn" data-direction="prev">← Prev</button>
      <h3 style="margin:0; color:#2563eb;">${monthNames[month]} ${year}</h3>
      <button class="calendar-nav-btn" data-direction="next">Next →</button>
    </div>
    <div class="calendar-grid">`;

  ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].forEach(d => {
    html += `<div style="font-weight:600;text-align:center;padding:0.5rem;">${d}</div>`;
  });

  for (let i = 0; i < firstDay; i++) html += '<div></div>';
  for (let day = 1; day <= daysInMonth; day++) html += `<div class="calendar-day">${day}</div>`;

  html += `</div></div>`;
  return html;
}

// Initialize calendar
document.addEventListener('DOMContentLoaded', initDatePicker);

function setFlightStatus(text) {
  const el = document.getElementById("flightStatus");
  if (el) el.textContent = text || "";
}

function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString([], { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function stopsLabel(stops) {
  if (stops === 0) return "Nonstop";
  if (stops === 1) return "1 stop";
  return `${stops} stops`;
}

// Your calendar currently outputs "M/D/YYYY - M/D/YYYY"
// Convert to "YYYY-MM-DD to YYYY-MM-DD"
function toISODate(mdyyyy) {
  // mdyyyy like "2/10/2026"
  const [m, d, y] = mdyyyy.split("/").map(s => s.trim());
  if (!m || !d || !y) return null;
  const mm = String(m).padStart(2, "0");
  const dd = String(d).padStart(2, "0");
  return `${y}-${mm}-${dd}`;
}

function normalizeDatesForBackend(datesStr) {
  // Accepts "M/D/YYYY - M/D/YYYY" OR already ISO format
  if (!datesStr) return "";

  // If already contains YYYY-MM-DD, leave it
  if (/\d{4}-\d{2}-\d{2}/.test(datesStr)) return datesStr;

  // Try parsing "M/D/YYYY - M/D/YYYY"
  const parts = datesStr.split("-").map(s => s.trim());
  if (parts.length < 2) return datesStr;

  const startISO = toISODate(parts[0]);
  const endISO = toISODate(parts[1]);
  if (!startISO || !endISO) return datesStr;

  return `${startISO} to ${endISO}`;
}

// Budget select values are "0-500", "500-1000", etc.
// Backend wants maxPrice (a number). We'll send the HIGH end.
function parseBudgetMax(budgetValue) {
  if (!budgetValue) return "";
  if (budgetValue.includes("+")) return ""; // treat as no max
  const [low, high] = budgetValue.split("-").map(s => s.trim());
  return high || "";
}

function renderFlights(data) {
  const container = document.getElementById("flightResults");
  if (!container) return;

  container.innerHTML = "";

  if (data.error) {
    container.innerHTML = `<div class="flight-error">${data.error}</div>`;
    return;
  }

  const offers = data.offers || [];
  if (offers.length === 0) {
    container.innerHTML = `<div class="flight-empty">No flights found.</div>`;
    return;
  }

  offers.forEach((offer) => {
    const out = offer.outbound;
    const inb = offer.inbound;

    const price = offer.price?.total ?? "?";
    const currency = offer.price?.currency ?? "USD";

    const airline = out?.airlines?.length ? out.airlines.join(", ") : "Airline unavailable";
    const codes = (offer.flightCodes || []).join(" • ");

    const card = document.createElement("div");
    card.className = "flight-card";
    card.innerHTML = `
      <div class="flight-card-top">
        <div>
          <div class="flight-price">${currency} ${price}</div>
          <div class="flight-airline">${airline}</div>
        </div>
        <div class="flight-codes">${codes}</div>
      </div>

      <div class="flight-legs">
        <div class="flight-leg">
          <div class="flight-leg-title">Outbound</div>
          <div class="flight-leg-route">${out?.from ?? ""} → ${out?.to ?? ""}</div>
          <div class="flight-leg-time">${fmtTime(out?.departAt)} → ${fmtTime(out?.arriveAt)}</div>
          <div class="flight-leg-meta">${stopsLabel(out?.stops ?? 0)} • ${out?.duration ?? ""}</div>
        </div>

        ${inb ? `
          <div class="flight-leg">
            <div class="flight-leg-title">Return</div>
            <div class="flight-leg-route">${inb?.from ?? ""} → ${inb?.to ?? ""}</div>
            <div class="flight-leg-time">${fmtTime(inb?.departAt)} → ${fmtTime(inb?.arriveAt)}</div>
            <div class="flight-leg-meta">${stopsLabel(inb?.stops ?? 0)} • ${inb?.duration ?? ""}</div>
          </div>
        ` : ""}
      </div>
    `;

    container.appendChild(card);
  });
}
