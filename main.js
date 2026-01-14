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
const exploreGrid = document.querySelector('.explore-placeholder');

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
    document.querySelector('.tab-btn[data-tab="plan"]').click();
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
