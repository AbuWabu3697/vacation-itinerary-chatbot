//tracking travel interests
let selectedInterests = [];

//start and end date
let datePickerMode = null;

//function for option button
document.querySelectorAll('.option-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    this.classList.toggle('active');
    const interest = this.textContent.trim();
    
    if (this.classList.contains('active')) {
      selectedInterests.push(interest);
      this.style.background = '#2563eb';
      this.style.color = '#ffffff';
      this.style.borderColor = '#2563eb';
    } else {
      selectedInterests = selectedInterests.filter(i => i !== interest);
      this.style.background = '#ffffff';
      this.style.color = '#1f2933';
      this.style.borderColor = '#d1d5db';
    }
  });
});

//function for send button
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

  //validation for required fields
  if (!destination || !dates || !budget) {
    alert('Please fill in destination, dates, and budget to continue.');
    return;
  }

  //display user message
  displayMessage(message, 'user');
  userInput.value = '';

  //generate bot response
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

//calendar popup
function initDatePicker() {
  const datesInput = document.getElementById('dates');
  datesInput.addEventListener('click', openCalendar);
}

function openCalendar() {
  const overlay = document.createElement('div');
  overlay.className = 'calendar-overlay';
  
  const calendarPopup = document.createElement('div');
  calendarPopup.className = 'calendar-popup';
  
  const today = new Date();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();
  
  calendarPopup.innerHTML = generateCalendarHTML(currentMonth, currentYear);
  
  overlay.appendChild(calendarPopup);
  document.body.appendChild(overlay);
  
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) {
      overlay.remove();
    }
  });
  
  document.querySelectorAll('.calendar-nav-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      overlay.remove();
      let newMonth = currentMonth + (this.dataset.direction === 'next' ? 1 : -1);
      let newYear = currentYear;
      
      if (newMonth > 11) {
        newMonth = 0;
        newYear++;
      } else if (newMonth < 0) {
        newMonth = 11;
        newYear--;
      }
      
      openCalendarMonth(newMonth, newYear);
    });
  });
  
  // Selecting start date from calendar
  document.querySelectorAll('.calendar-day').forEach(day => {
    day.addEventListener('click', function() {
      if (this.textContent) {
        const startDate = `${currentMonth + 1}/${this.textContent}/${currentYear}`;
        const datesInput = document.getElementById('dates');
        datesInput.value = startDate;
        
        // Show prompt for end date
        setTimeout(() => {
          alert('Now select your end date');
          overlay.remove();
          setTimeout(() => openEndCalendar(), 300);
        }, 200);
      }
    });
  });
}

function openEndCalendar() {
  const overlay = document.createElement('div');
  overlay.className = 'calendar-overlay';
  
  const calendarPopup = document.createElement('div');
  calendarPopup.className = 'calendar-popup';
  
  const today = new Date();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();
  
  calendarPopup.innerHTML = generateCalendarHTML(currentMonth, currentYear);
  
  overlay.appendChild(calendarPopup);
  document.body.appendChild(overlay);
  
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) {
      overlay.remove();
    }
  });
  
  // Calendar navigation for end date
  document.querySelectorAll('.calendar-nav-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      overlay.remove();
      let newMonth = currentMonth + (this.dataset.direction === 'next' ? 1 : -1);
      let newYear = currentYear;
      
      if (newMonth > 11) {
        newMonth = 0;
        newYear++;
      } else if (newMonth < 0) {
        newMonth = 11;
        newYear--;
      }
      
      openEndCalendarMonth(newMonth, newYear);
    });
  });
  
  // Selecting end date from calendar
  document.querySelectorAll('.calendar-day').forEach(day => {
    day.addEventListener('click', function() {
      if (this.textContent) {
        const endDate = `${currentMonth + 1}/${this.textContent}/${currentYear}`;
        const datesInput = document.getElementById('dates');
        const startDate = datesInput.value;
        datesInput.value = `${startDate} - ${endDate}`;
        overlay.remove();
      }
    });
  });
}

function generateCalendarHTML(month, year) {
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  
  let html = `
    <div style="padding: 1.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <button class="calendar-nav-btn" data-direction="prev">← Prev</button>
        <h3 style="margin: 0; color: #2563eb;">${monthNames[month]} ${year}</h3>
        <button class="calendar-nav-btn" data-direction="next">Next →</button>
      </div>
      <div class="calendar-grid">
  `;
  
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  dayLabels.forEach(day => {
    html += `<div style="font-weight: 600; text-align: center; padding: 0.5rem;">${day}</div>`;
  });
  
  for (let i = 0; i < firstDay; i++) {
    html += '<div></div>';
  }
  
  for (let day = 1; day <= daysInMonth; day++) {
    html += `<div class="calendar-day">${day}</div>`;
  }
  
  html += `</div></div>`;
  return html;
}

function openCalendarMonth(month, year) {
  const overlay = document.createElement('div');
  overlay.className = 'calendar-overlay';
  
  const calendarPopup = document.createElement('div');
  calendarPopup.className = 'calendar-popup';
  calendarPopup.innerHTML = generateCalendarHTML(month, year);
  
  overlay.appendChild(calendarPopup);
  document.body.appendChild(overlay);
  
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) overlay.remove();
  });
  
  //calendar navigation
  document.querySelectorAll('.calendar-nav-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      overlay.remove();
      let newMonth = month + (this.dataset.direction === 'next' ? 1 : -1);
      let newYear = year;
      
      if (newMonth > 11) {
        newMonth = 0;
        newYear++;
      } else if (newMonth < 0) {
        newMonth = 11;
        newYear--;
      }
      
      openCalendarMonth(newMonth, newYear);
    });
  });
  
  //selecting start date
  document.querySelectorAll('.calendar-day').forEach(day => {
    day.addEventListener('click', function() {
      if (this.textContent) {
        const startDate = `${month + 1}/${this.textContent}/${year}`;
        const datesInput = document.getElementById('dates');
        datesInput.value = startDate;
        
        setTimeout(() => {
          alert('Now select your end date');
          overlay.remove();
          setTimeout(() => openEndCalendar(), 300);
        }, 200);
      }
    });
  });
}

function openEndCalendarMonth(month, year) {
  const overlay = document.createElement('div');
  overlay.className = 'calendar-overlay';
  
  const calendarPopup = document.createElement('div');
  calendarPopup.className = 'calendar-popup';
  calendarPopup.innerHTML = generateCalendarHTML(month, year);
  
  overlay.appendChild(calendarPopup);
  document.body.appendChild(overlay);
  
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) overlay.remove();
  });
  
  document.querySelectorAll('.calendar-nav-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      overlay.remove();
      let newMonth = month + (this.dataset.direction === 'next' ? 1 : -1);
      let newYear = year;
      
      if (newMonth > 11) {
        newMonth = 0;
        newYear++;
      } else if (newMonth < 0) {
        newMonth = 11;
        newYear--;
      }
      
      openEndCalendarMonth(newMonth, newYear);
    });
  });
  
  //selecting end date
  document.querySelectorAll('.calendar-day').forEach(day => {
    day.addEventListener('click', function() {
      if (this.textContent) {
        const endDate = `${month + 1}/${this.textContent}/${year}`;
        const datesInput = document.getElementById('dates');
        const startDate = datesInput.value;
        datesInput.value = `${startDate} - ${endDate}`;
        overlay.remove();
      }
    });
  });
}

//initialize calendar on page load
document.addEventListener('DOMContentLoaded', initDatePicker);