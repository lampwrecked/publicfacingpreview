import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Sorted set: each member is an email, score is its signup timestamp.
// Auto-dedupes (same email re-submitted just updates its timestamp).
const KEY = "publicfacing:subscribers";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const body = req.body ?? {};
    const raw = typeof body.email === "string" ? body.email.trim() : "";

    if (!raw || raw.length > 254 || !EMAIL_RE.test(raw)) {
      return res.status(400).json({ error: "Invalid email" });
    }

    const email = raw.toLowerCase();
    const now = Date.now();

    // Returns 1 if newly added, 0 if already present (score got updated)
    const added = await redis.zadd(KEY, { score: now, member: email });

    return res.status(200).json({ ok: true, isNew: added === 1 });
  } catch (err) {
    console.error("subscribe error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}
