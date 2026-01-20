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




async function handleSendMessage() {
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

  const loadingMsg = displayMessage("Generating your itinerary...", 'bot');

  try {
    // API call to backend
    const response = await fetch('/api/generate-itinerary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        destination,
        dates,
        budget,
        transport,
        interests: selectedInterests,
        message
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to generate itinerary');
    }

    loadingMsg.remove();
    displayMessage(data.message, 'bot');
    
    renderItinerary(data.itinerary);

  } catch (error) {
    console.error('Error:', error);
    loadingMsg.remove();
    displayMessage(`❌ Error: ${error.message}`, 'bot');
  }

  searchFlights();
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
 return `Great! I'm planning a trip to ${destination} from ${dates} with a $${budget} budget
 Transportation: ${transport}
 Your interests: ${interests.length > 0 ? interests.join(', ') : 'general sightseeing'}
 Special requests: ${userMessage}

Your personalized itinerary is being generated...`;
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




const allCities = [
 {name: "Paris", image: "https://loveincorporated.blob.core.windows.net/contentimages/fullsize/a8a9bce0-de89-417e-a65e-ecdaf23d1d59-paris-full-guide-update.jpg"},
 {name: "Tokyo", image: "https://wallpaperaccess.com/full/44164.jpg"},
 {name: "New York", image: "https://th.bing.com/th/id/R.cf34b93eb0a87fe2085efa649a47d521?rik=elSp%2bjkA%2fEBZfg&riu=http%3a%2f%2fbpc.h-cdn.co%2fassets%2f17%2f23%2f1600x800%2flandscape-1496690479-new-york-tourist-attractions.jpg&ehk=d4JFcY9X9JtMK1q7rWEbMjyZdOTPxQTN%2brP1qqHkwNw%3d&risl=&pid=ImgRaw&r=0"},
 {name: "London", image: "https://cdn.unifiedcommerce.com/content/product/large/5900511104042.jpg"},
 {name: "Barcelona", image: "https://wallpaperaccess.com/full/1322174.jpg"},
 {name: "Rome", image: "https://img.ex.co/image/upload/v1706818824/hv3rfvephstjqdmm3wft.jpg"},
 {name: "Amsterdam", image: "https://misstourist.com/wp-content/uploads/2023/12/2-1-Canal-Belt-Grachtengordel-%E2%80%93-best-area-for-couples-660x435@2x.jpg"},
 {name: "Berlin", image: "https://lp-cms-production.imgix.net/2019-06/GettyImages-475150263_super.jpg?auto=compress&fit=crop&fm=auto&sharp=10&vib=20&w=1200&h=800"},
 {name: "Sydney", image: "https://wallpapercave.com/wp/wp2684726.jpg"},
 {name: "Dubai", image: "https://wallpaperaccess.com/full/1735114.jpg"},
 {name: "Bangkok", image: "https://www.tripsavvy.com/thmb/ZtwK0eWCSDo4DQjEGi-IupGJ2I0=/5472x3648/filters:no_upscale():max_bytes(150000):strip_icc()/wat-arun-temple-bangkok-5c461eee46e0fb00016fe445.jpg"},
 {name: "Singapore", image: "https://www.stokedtotravel.com/wp-content/uploads/2020/11/Singapore-1.jpg"},
 {name: "Istanbul", image: "https://media.istockphoto.com/photos/stanbul-turkey-picture-id458012057?b=1&k=20&m=458012057&s=170667a&w=0&h=zBrkAjxV8Ser_DKekq6g9EWuPgXsNc8qktI3rpwoj0g="},
 {name: "Prague", image: "https://www.siliconrepublic.com/wp-content/uploads/2018/06/Prague_shutterstock_696131494-718x523.jpg"},
 {name: "Vienna", image: "https://tse4.mm.bing.net/th/id/OIP._WIfrR7zlI-s-kI9G9jxlAHaEK?w=1440&h=810&rs=1&pid=ImgDetMain&o=7&rm=3"},
 {name: "Hong Kong", image: "https://www.discoverhongkong.com/content/dam/dhk/intl/explore/tips-for-making-your-trip-to-hong-kong/tips-for-making-your-trip-to-hong-kong-1920x1080.jpg"},
 {name: "Lisbon", image: "https://wallpaperaccess.com/full/6712385.jpg"},
 {name: "Seoul", image: "https://www.agoda.com/wp-content/uploads/2024/08/Han-River-seoul-korea-1126x700-1.jpg"},
 {name: "Los Angeles", image: "https://s3.amazonaws.com/mentoring.redesign/s3fs-public/los-angeles.jpg"},
 {name: "Chicago", image: "https://gregbenzphotography.com/wp-content/uploads/2011/03/The-Bean-and-the-Chicago-Skyline.jpg"},
 {name: "Rio De Janiero", image: "https://cdn.britannica.com/03/94403-050-03683FB0/Rio-de-Janeiro-Braz.jpg"},
 {name: "Cape Town", image: "https://www.earthsattractions.com/wp-content/uploads/2017/11/V_A_Waterfront-870x540.jpg"},
 {name: "Vancouver", image: "https://www.tripsavvy.com/thmb/DnXZn47c_DgjZWN50MzwZ4X2vT4=/960x0/filters:no_upscale():max_bytes(150000):strip_icc()/GettyImages-629829924-5bdb57f74cedfd0026ae431f.jpg"},
 {name: "Mexico City", image: "https://visitingmexico.com/wp-content/uploads/CDMX-scaled.jpeg"},
 {name: "Buenos Aires", image: "https://tse4.mm.bing.net/th/id/OIP.OgcsoZbwNF1Jo_gK4ZpiywHaFR?rs=1&pid=ImgDetMain&o=7&rm=3"},
 {name: "Moscow", image: "https://th.bing.com/th/id/R.88a84c08a8fecbd255b672d1d288da73?rik=3KgrNpjTVwOWCA&riu=http%3a%2f%2fwww.businessdestinations.com%2fwp-content%2fuploads%2f2015%2f02%2fMoscow.jpg&ehk=YNfQ7l5qpMwf7q6ED5ckY51DSRFL43xceZiBZAp3FA0%3d&risl=&pid=ImgRaw&r=0"},
 {name: "Athens", image: "https://tse4.mm.bing.net/th/id/OIP.TTGRnCk5fDpeblPAFOR4jgHaFj?rs=1&pid=ImgDetMain&o=7&rm=3"},
 {name: "Cairo", image: "https://media.cntraveler.com/photos/655cdf1d2d09a7e0b27741b5/16:9/w_2560%2Cc_limit/Cairo%2520Egypt_GettyImages-1370918272.jpg"},
 {name: "Budapest", image: "https://completecityguides.com/images/blog/full/best-europe-destinations/budapest-chain-bridge.jpg"},
 {name: "Miami", image: "https://tse1.mm.bing.net/th/id/OIP.ILRTrQmOGq8Sq-quxVhquwHaE8?rs=1&pid=ImgDetMain&o=7&rm=3"}
];




// Load favorites from localStorage
let favorites = JSON.parse(localStorage.getItem('favoriteCities')) || [];




function toggleFavorite(cityName, event) {
 event.stopPropagation();
 if (favorites.includes(cityName)) {
   favorites = favorites.filter(fav => fav !== cityName);
 } else {
   favorites.push(cityName);
 }
 localStorage.setItem('favoriteCities', JSON.stringify(favorites));
 renderCityGrid();
}




function getSortedCities() {
 // Separate favorites and non-favorites
 const favCities = allCities.filter(city => favorites.includes(city.name));
 const nonFavCities = allCities.filter(city => !favorites.includes(city.name));
 // Favorites at top, then rest
 return [...favCities, ...nonFavCities];
}




function renderCityGrid() {
 exploreGrid.innerHTML = '';
 const sortedCities = getSortedCities();
 sortedCities.forEach(cityObj => {
   const card = document.createElement('div');
   card.className = 'city-card';
   if (favorites.includes(cityObj.name)) {
     card.classList.add('favorited');
   }
 
   const img = document.createElement('img');
   img.src = cityObj.image;
   img.alt = cityObj.name;
 
   const heartBtn = document.createElement('button');
   heartBtn.className = 'heart-btn';
   heartBtn.innerHTML = favorites.includes(cityObj.name) ? '❤️' : '🤍';
   heartBtn.addEventListener('click', (e) => toggleFavorite(cityObj.name, e));
 
   const cityName = document.createElement('div');
   cityName.textContent = cityObj.name;
 
   card.appendChild(img);
   card.appendChild(heartBtn);
   card.appendChild(cityName);
 
   card.addEventListener('click', () => {
     document.getElementById('destination').value = cityObj.name;
     openCityModal(cityObj);
   });
 
   exploreGrid.appendChild(card);
 });
}




renderCityGrid();




// ---------------- City Modal Logic ----------------
function getCityDetails(name) {
 const db = {
   'Paris': {
     attractions: ['Eiffel Tower', 'Louvre Museum', 'Montmartre'],
     food: ['Croissants at a local bakery', 'Eclairs', 'Macarons'],
     sightseeing: ['Seine River Cruise', 'Notre-Dame Area', 'Palais-Royal Gardens']
   },
   'Tokyo': {
     attractions: ['Senso-ji Temple', 'Meiji Shrine', 'Shibuya Crossing'],
     food: ['Sushi at Tsukiji', 'Ramen alleys', 'Yakitori at Izakayas'],
     sightseeing: ['Tokyo Skytree', 'Ueno Park', 'Imperial Palace']
   },
   'New York': {
     attractions: ['Statue of Liberty', 'Central Park', 'Metropolitan Museum'],
     food: ['Street Bagels', '$1 Pizza Slices', 'Fine dining in Manhattan'],
     sightseeing: ['Brooklyn Bridge Walk', 'Alcatraz', 'Times Square']
   },
   'Rome': {
     attractions: ['Colosseum', 'Roman Forum', 'Vatican Museums'],
     food: ['Carbonara', 'Gelato', 'Cacio e Pepe'],
     sightseeing: ['Piazza Navona', 'Trevi Fountain', 'Spanish Steps']
   },
   'London': {
     attractions: ['Buckingham Palace', 'Tower of London', 'British Museum'],
     food: ['Fish and chips', 'Full English breakfast', 'Afternoon tea'],
     sightseeing: ['Big Ben', 'London Eye', 'Tower Bridge']
   },
   'Barcelona': {
     attractions: ['Sagrada Familia', 'Park Guell', 'Las Ramblas'],
     food: ['Paella', 'Tapas bars', 'Churros'],
     sightseeing: ['Gothic Quarter', 'Montjuic Hill', 'Casa Batlló']
   },
   'Amsterdam': {
     attractions: ['Anne Frank House', 'Van Gogh Museum', 'Rijksmuseum'],
     food: ['Stroopwafels', 'Bitterballen', 'Poffertjes'],
     sightseeing: ['Canal Ring', 'Vondelpark', 'Jordaan']
   },
   'Berlin': {
     attractions: ['Brandenburg Gate', 'Museum Island', 'Reichstag Building'],
     food: ['Currywurst', 'Döner Kebab', 'Schnitzel'],
     sightseeing: ['Berlin Wall Memorial', 'Potsdamer Platz', 'East Side Gallery']
   },
   'Sydney': {
     attractions: ['Sydney Opera House', 'Sydney Harbour Bridge', 'Taronga Zoo'],
     food: ['Fish and chips', 'Meat pies', 'Vegemite on toast'],
     sightseeing: ['Bondi Beach', 'The Rocks', 'Darling Harbour']
   },
   'Dubai': {
     attractions: ['Burj Khalifa', 'Dubai Mall', 'Desert Safari'],
     food: ['Shawarma', 'Kabsa', 'Machboos'],
     sightseeing: ['Dubai Fountain', 'Palm Jumeirah', 'Dubai Creek']
   },
   'Bangkok': {
     attractions: ['Grand Palace', 'Wat Pho', 'Chatuchak Weekend Market'],
     food: ['Pad Thai', 'Som Tam', 'Mango Sticky Rice'],
     sightseeing: ['Chinatown', 'Lumpini Park', 'Suan Lum Night Market']
   },
   'Singapore': {
     attractions: ['Gardens by the Bay', 'Marina Bay Sands', 'Chinatown'],
     food: ['Hainanese Chicken Rice', 'Laksa', 'Rendang'],
     sightseeing: ['Sentosa Island', 'Orchard Road', 'Marina Bay']
   },
   'Istanbul': {
     attractions: ['Hagia Sophia', 'Blue Mosque', 'Grand Bazaar'],
     food: ['Baklava', 'Kofte', 'Manti'],
     sightseeing: ['Bosphorus Cruise', 'Topkapi Palace', 'Galata Bridge']
   },
   'Prague': {
     attractions: ['Prague Castle', 'Charles Bridge', 'Old Town Square'],
     food: ['Trdelník', 'Goulash', 'Czech Beer'],
     sightseeing: ['Prague Astronomical Clock', 'Wenceslas Square', 'Petřin Hill']
   },
   'Vienna': {
     attractions: ['Schönbrunn Palace', 'St. Stephen’s Cathedral', 'Belvedere Palace'],
     food: ['Wiener Schnitzel', 'Sachertorte', 'Apfelstrudel'],
     sightseeing: ['Vienna State Opera', 'Hofburg Palace', 'Naschmarkt']
   },
   'Hong Kong': {
     attractions: ['Victoria Peak', 'Tian Tan Buddha (Big Buddha)', 'Hong Kong Disneyland'],
     food: ['Dim Sum', 'Roast Goose', 'Egg Tarts'],
     sightseeing: ['Victoria Harbour', 'Star Ferry', 'Temple Street Night Market']
   },
   'Lisbon': {
     attractions: ['Belém Tower', 'Jerónimos Monastery', 'Rossio Square'],
     food: ['Pastel de Nata', 'Francesinha', 'Bacalhau'],
     sightseeing: ['Lisbon Cathedral', 'Miradouros', 'Tram 28']
   },
   'Seoul': {
     attractions: ['Gyeongbokgung Palace', 'Bukchon Hanok Village', 'N Seoul Tower'],
     food: ['Tteokbokki', 'Kimchi', 'Korean BBQ'],
     sightseeing: ['Gangnam District', 'Myeongdong', 'Hongdae']
   },
   'Los Angeles': {
     attractions: ['Hollywood Sign', 'Universal Studios', 'Getty Center'],
     food: ['Street Tacos', 'In-N-Out Burger', 'Food truck fusion'],
     sightseeing: ['Santa Monica Pier', 'Venice Beach', 'Griffith Observatory']
   },
   'Chicago': {
     attractions: ['Millennium Park (The Bean)', 'Art Institute of Chicago', 'Navy Pier'],
     food: ['Deep-dish pizza', 'Chicago-style hot dogs', 'Italian beef sandwiches'],
     sightseeing: ['Chicago Riverwalk', 'Skydeck at Willis Tower', 'Magnificent Mile']
   },
   'Rio De Janeiro': {
     attractions: ['Christ the Redeemer', 'Sugarloaf Mountain', 'Copacabana Beach'],
     food: ['Feijoada', 'Pão de Açúcar', 'Açaí Bowl'],
     sightseeing: ['Selarón Steps', 'Lapa Arches', 'Ipanema Beach']
   },
   'Cape Town': {
     attractions: ['Table Mountain', 'Robben Island', 'Cape of Good Hope'],
     food: ['Braai', 'Bobotie', 'Malva Pudding'],
     sightseeing: ['V&A Waterfront', 'Cape Town Stadium', 'District Six Museum']
   },
   'Vancouver': {
     attractions: ['Stanley Park', 'Capilano Suspension Bridge', 'Granville Island'],
     food: ['Salmon dishes', 'Poutine', 'Sushi'],
     sightseeing: ['Gastown Steam Clock', 'English Bay', 'Grouse Mountain']
   },
   'Mexico City': {
     attractions: ['Zócalo', 'Teotihuacán', 'Palacio de Bellas Artes'],
     food: ['Tacos al Pastor', 'Mole Poblano', 'Chiles en Nogada'],
     sightseeing: ['Palacio de Bellas Artes', 'Templo Mayor', 'Catedral Metropolitana']
   },
   'Buenos Aires': {
     attractions: ['Casa Rosada', 'Teatro Colón', 'Recoleta Cemetery'],
     food: ['Asado', 'Empanadas', 'Dulce de Leche desserts'],
     sightseeing: ['La Boca (Caminito)', 'Puerto Madero', 'Palermo Parks']
   },
   'Moscow': {
     attractions: ['Red Square', 'The Kremlin', 'St. Basil\'s Cathedral'],
     food: ['Borscht', 'Pelmeni', 'Caviar'],
     sightseeing: ['Tretyakov Gallery', 'Gorky Park', 'The Bolshoi Theatre']
   },
   'Athens': {
     attractions: ['Acropolis of Athens', 'Parthenon', 'Temple of Hephaestus'],
     food: ['Greek Salad', 'Souvlaki', 'Baklava'],
     sightseeing: ['Acropolis Museum', 'Plaka District', 'Syntagma Square']
   },
   'Cairo': {
     attractions: ['Pyramids of Giza', 'Khan El-Khalili', 'Islamic Cairo'],
     food: ['Ful Medames', 'Taameya', 'Koshari'],
     sightseeing: ['Great Pyramid', 'Sphinx', 'Egyptian Museum']
   },
   'Budapest': {
     attractions: ['Budapest Castle', 'Margaret Island', 'St. Stephen\'s Basilica'],
     food: ['Goulash', 'Langos', 'Paprika'],
     sightseeing: ['Buda Castle', 'Chain Bridge', 'Dohány Street Synagogue']
   },
   'Miami': {
     attractions: ['South Beach', 'Art Deco Historic District', 'Wynwood Walls'],
     food: ['Cuban Sandwiches', 'Key Lime Pie', 'Seafood'],
     sightseeing: ['Ocean Drive', 'Vizcaya Museum', 'Little Havana']
   }
 };

 return db[name] || {
   attractions: ['Historic center', 'Popular museums', 'Local parks'],
   food: ['Top local dishes', 'Street food highlights', 'Well-rated cafes'],
   sightseeing: ['City viewpoints', 'Architectural highlights', 'Evening entertainment']
 };
}


function openCityModal(cityObj) {
 const modal = document.getElementById('cityModal');
 if (!modal) return;


 const img = document.getElementById('cityModalImg');
 const title = document.getElementById('cityModalTitle');
 const attractionsEl = document.getElementById('cityAttractions');
 const foodEl = document.getElementById('cityFood');
 const sightEl = document.getElementById('citySightseeing');


 img.src = cityObj.image || '';
 img.alt = cityObj.name || '';
 title.textContent = cityObj.name || '';


 const details = getCityDetails(cityObj.name);


 // populate lists
 attractionsEl.innerHTML = details.attractions.map(a => `<li>${a}</li>`).join('');
 foodEl.innerHTML = details.food.map(f => `<li>${f}</li>`).join('');
 sightEl.innerHTML = details.sightseeing.map(s => `<li>${s}</li>`).join('');


 modal.style.display = 'flex';
 modal.setAttribute('aria-hidden', 'false');


 // close handlers
 const closeBtn = modal.querySelector('.city-modal-close');
 function onClose() { closeCityModal(); }
 closeBtn.addEventListener('click', onClose, { once: true });


 // click outside to close
 function onOverlayClick(e) {
   if (e.target === modal) closeCityModal();
 }
 modal.addEventListener('click', onOverlayClick, { once: true });


 // esc to close
 function onEsc(e) {
   if (e.key === 'Escape') closeCityModal();
 }
 document.addEventListener('keydown', onEsc, { once: true });


 // helper to remove handlers inside closeCityModal
 function closeCityModal() {
   modal.style.display = 'none';
   modal.setAttribute('aria-hidden', 'true');
 }
}




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



