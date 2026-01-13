import Groq from "groq-sdk";

console.log("START");

if (!process.env.GROQ_API_KEY) {
  console.error("NO_KEY: set GROQ_API_KEY in this terminal first");
  process.exit(1);
}

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
  console.log("CALLING...");

  const stream = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: "why is the sky blue?" }],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices?.[0]?.delta?.content ?? "");
  }

  process.stdout.write("\nDONE\n");
}

main().catch((err) => {
  console.error("\nERROR:\n", err);
  process.exit(1);
});
