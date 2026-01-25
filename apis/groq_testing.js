import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const BASE_URL = "http://127.0.0.1:5000";

// --- helpers ---
async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { json = { raw: text }; }

  if (!res.ok) {
    const err = new Error(`HTTP ${res.status} on ${path}`);
    err.status = res.status;
    err.payload = json;
    throw err;
  }
  return json;
}

async function safeCall(name, fn) {
  try {
    const data = await fn();
    return { ok: true, name, data };
  } catch (e) {
    return {
      ok: false,
      name,
      error: {
        message: e.message,
        status: e.status,
        payload: e.payload,
      },
    };
  }
}

// --- build LLM prompt ---
function buildItineraryPrompt({ userInput, results }) {
  const flights = results.find(r => r.name === "flights");
  const hotels  = results.find(r => r.name === "hotels");
  const transfers = results.find(r => r.name === "transfers");
  const activities = results.find(r => r.name === "activities");

  return `
You are an expert travel planner.

GOAL:
Create the best possible itinerary. Use real API data when available.
If flights or transfers data is missing or errored, estimate plausible options instead.
When you estimate, you MUST label it clearly as "ESTIMATE" and explain assumptions.

USER INPUT:
${JSON.stringify(userInput, null, 2)}

API RESULTS:
Flights:
${JSON.stringify(flights, null, 2)}

Hotels:
${JSON.stringify(hotels, null, 2)}

Transfers:
${JSON.stringify(transfers, null, 2)}

Activities:
${JSON.stringify(activities, null, 2)}

OUTPUT FORMAT (JSON ONLY):
{
  "summary": {
    "destination": string,
    "dates": string,
    "budget": string,
    "assumptions": [string]
  },
  "cost_breakdown": {
    "flights": { "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string },
    "hotels": { "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string },
    "local_transport": { "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string },
    "food": { "type": "ESTIMATE", "range_usd": [number, number], "notes": string },
    "activities": { "type": "REAL|ESTIMATE", "range_usd": [number, number], "notes": string },
    "total_estimated": { "range_usd": [number, number] }
  },
  "itinerary": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "morning": [string],
      "afternoon": [string],
      "evening": [string],
      "notes": [string]
    }
  ],
  "recommended_hotels": [
    { "name": string, "why": string, "price_total_usd": number|null, "source": "REAL|ESTIMATE" }
  ],
  "flight_plan": {
    "source": "REAL|ESTIMATE",
    "options": [
      { "summary": string, "price_usd": number|null, "notes": string }
    ]
  },
  "transfer_plan": {
    "source": "REAL|ESTIMATE",
    "options": [
      { "summary": string, "price_usd": number|null, "notes": string }
    ]
  }
}

Hard rules:
- Use REAL prices only if present in API results.
- If missing, provide reasonable ranges (ESTIMATE) and label them.
- Keep it practical (travel times, neighborhoods, clustering).
- No markdown. JSON only.
`.trim();
}

// --- main planner ---
export async function planTrip(userInput) {
  // call your Flask routes in parallel (safe)
  const results = await Promise.all([
    safeCall("flights", () => postJSON("/api/flights", {
      origin: userInput.origin,
      destination: userInput.destination,
      dates: userInput.dates,
      budget: userInput.budget
    })),
    safeCall("hotels", () => postJSON("/api/hotels", {
      destination: userInput.destination,
      dates: userInput.dates,
      budget: userInput.budget
    })),
    safeCall("transfers", () => postJSON("/api/transfers", {
      start_location: userInput.origin,           // or airport
      end_location: userInput.destination,        // or address
      dates: userInput.dates
    })),
    safeCall("activities", () => postJSON("/api/activities", {
      destination: userInput.destination,
      interests: userInput.interests
    })),
  ]);

  const prompt = buildItineraryPrompt({ userInput, results });

  const stream = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "system", content: "Return only valid JSON. No markdown, no commentary." },
      { role: "user", content: prompt },
    ],
    temperature: 0.7,
    stream: true,
  });

  let full = "";
  for await (const chunk of stream) {
    const token = chunk.choices?.[0]?.delta?.content ?? "";
    process.stdout.write(token);
    full += token;
  }
  process.stdout.write("\n");

  // optional: try to parse to ensure it's valid JSON
  try {
    return JSON.parse(full);
  } catch {
    // if the model outputs slightly invalid JSON, you can add a repair pass
    return { error: "Model output was not valid JSON", raw: full, results };
  }
}
