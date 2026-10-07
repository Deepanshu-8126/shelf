/**
 * Cloudflare Worker: 100% Free Serverless Telegram-to-GitHub Actions Bridge
 * Runs 24/7 in the cloud with ZERO PC, ZERO Server Cost (100,000 requests/day free).
 * Forwards Telegram button clicks & commands directly to GitHub Actions repository_dispatch!
 */

const GITHUB_REPO = "Deepanshu-8126/dk_hu"; // Your GitHub Repo
const BOT_TOKEN = "8809830963:AAG22CFChal-D13uSkNLUmCoyHD3FGvgWjY";
// You can set GITHUB_PAT as an environment variable in Cloudflare Worker Settings
// or paste a Classic PAT with 'repo' scope.

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Super YouTube Agent Serverless Telegram Bridge Active 🚀", { status: 200 });
    }

    try {
      const update = await request.json();
      const token = env.TELEGRAM_BOT_TOKEN || BOT_TOKEN;
      const ghPat = env.GITHUB_PAT || "";

      // Handle Callback Queries (Button Clicks)
      if (update.callback_query) {
        const cq = update.callback_query;
        const chatId = cq.message.chat.id;
        const data = cq.data;

        // Acknowledge tap
        await fetch(`https://api.telegram.org/bot${token}/answerCallbackQuery`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ callback_query_id: cq.id, text: "Triggering Cloud Runner... 🚀" })
        });

        // Trigger GitHub Actions
        if (data.startsWith("run_ch7_") || data === "draft_confirm_render") {
          let actionType = "next";
          let niche = "python";
          if (data === "run_ch7_auto") actionType = "auto";
          if (data === "run_ch7_java") { actionType = "niche"; niche = "java"; }
          if (data === "run_ch7_ai") { actionType = "niche"; niche = "ai_tools"; }

          if (ghPat) {
            await fetch(`https://api.github.com/repos/${GITHUB_REPO}/dispatches`, {
              method: "POST",
              headers: {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": `Bearer ${ghPat}`,
                "User-Agent": "Telegram-CF-Worker"
              },
              body: JSON.stringify({
                event_type: "render_coding_short",
                client_payload: { action: actionType, niche: niche }
              })
            });

            await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                chat_id: chatId,
                text: `⏳ *[GitHub Cloud Execution Started]*\n\nPC is OFF! GitHub Cloud runner has started rendering your video in the background.\n\nVideo will be delivered here automatically in ~1.5 mins! 🎬`,
                parse_mode: "Markdown"
              })
            });
          }
        }
      }

      return new Response("OK", { status: 200 });
    } catch (err) {
      return new Response(`Error: ${err.message}`, { status: 500 });
    }
  }
};
