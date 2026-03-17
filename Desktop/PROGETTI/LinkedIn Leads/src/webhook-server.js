const express = require("express");
const crypto = require("crypto");
const path = require("path");
const { config } = require("./config");
const { updateLeadStatus, getLeads } = require("./store");
const { sendWelcomeMessage } = require("./messenger");
const { getDefaultAccount } = require("./accounts");
const { log, logWebhook } = require("./logger");
const { registerApiRoutes } = require("./api-routes");
const { humanRandom } = require("./human-delay");

function basicAuthMiddleware(req, res, next) {
  const { user, pass } = config.dashboard;
  if (!user || !pass) return next();

  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Basic ")) {
    res.set("WWW-Authenticate", 'Basic realm="LinkedIn Leads Dashboard"');
    return res.status(401).send("Authentication required");
  }

  const decoded = Buffer.from(authHeader.slice(6), "base64").toString("utf-8");
  const [inputUser, inputPass] = decoded.split(":");

  const userMatch = crypto.timingSafeEqual(Buffer.from(inputUser), Buffer.from(user));
  const passMatch = crypto.timingSafeEqual(Buffer.from(inputPass), Buffer.from(pass));
  if (!userMatch || !passMatch) {
    res.set("WWW-Authenticate", 'Basic realm="LinkedIn Leads Dashboard"');
    return res.status(401).send("Invalid credentials");
  }

  next();
}

function createWebhookServer() {
  const app = express();

  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  app.use(express.text());

  // Health check — no auth
  app.get("/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // Protect dashboard and API routes with basic auth
  app.use("/dashboard", basicAuthMiddleware);
  app.use("/api", basicAuthMiddleware);

  // Dashboard SPA — serve static files from dashboard/dist
  const dashboardDistPath = path.join(__dirname, "..", "dashboard", "dist");
  app.use("/dashboard", express.static(dashboardDistPath));
  app.get("/dashboard/{*splat}", (_req, res) => {
    res.sendFile(path.resolve(dashboardDistPath, "index.html"));
  });

  // Register all REST API routes
  registerApiRoutes(app);

  // Webhook endpoint with accountId parameter
  app.post("/webhooks/unipile/:accountId", async (req, res) => {
    try {
      const { accountId } = req.params;
      const event = req.body;
      if (!event || typeof event !== "object") {
        log("warn", "Webhook received empty or non-JSON body", {
          accountId,
          contentType: req.headers["content-type"],
          body: String(req.body ?? "").substring(0, 200),
        });
        return res.status(200).json({ received: true, ignored: true });
      }
      logWebhook({ action: "received", accountId, eventType: event.event || event.type, data: event });
      log("info", `Webhook received: ${event.event || event.type || "unknown"}`, {
        accountId,
        body: JSON.stringify(event).substring(0, 500),
      });
      await handleWebhookEvent(accountId, event);
      res.status(200).json({ received: true });
    } catch (error) {
      log("error", "Webhook processing error", { accountId: req.params.accountId, error: error.message });
      res.status(500).json({ error: "Internal processing error" });
    }
  });

  // Backward compat: old webhook route without accountId uses default account
  app.post("/webhooks/unipile", async (req, res) => {
    try {
      const defaultAccount = getDefaultAccount();
      const accountId = defaultAccount.id;
      const event = req.body;
      if (!event || typeof event !== "object") {
        log("warn", "Webhook received empty or non-JSON body", {
          accountId,
          contentType: req.headers["content-type"],
          body: String(req.body ?? "").substring(0, 200),
        });
        return res.status(200).json({ received: true, ignored: true });
      }
      logWebhook({ action: "received", accountId, eventType: event.event || event.type, data: event });
      log("info", `Webhook received: ${event.event || event.type || "unknown"}`, {
        accountId,
        body: JSON.stringify(event).substring(0, 500),
      });
      await handleWebhookEvent(accountId, event);
      res.status(200).json({ received: true });
    } catch (error) {
      log("error", "Webhook processing error", { error: error.message });
      res.status(500).json({ error: "Internal processing error" });
    }
  });

  return app;
}

async function handleWebhookEvent(accountId, event) {
  const eventType = event.event || event.type || "";
  if (
    eventType.includes("relation") ||
    eventType.includes("connection") ||
    eventType.includes("invitation_accepted")
  ) {
    await handleConnectionAccepted(accountId, event);
    return;
  }
  if (eventType.includes("message") && event.data) {
    await handleNewMessage(accountId, event);
    return;
  }
  log("info", `Unhandled webhook event: ${eventType}`, { accountId });
}

async function handleConnectionAccepted(accountId, event) {
  // Unipile webhook fields are directly on event (not event.data)
  const data = event.data || event;
  const identifier =
    data.user_public_identifier || data.public_identifier ||
    data.user_id || data.identifier;
  if (!identifier) { log("warn", "Connection event without identifier", { accountId, event }); return; }
  log("info", `Connection accepted by: ${identifier} (${data.user_full_name || ""})`, { accountId });
  const leads = getLeads(accountId);
  const lead = leads.find(
    (l) => l.identifier === identifier || l.identifier === data.user_public_identifier
  );
  if (!lead) {
    log("warn", `Connection accepted by unknown lead: ${identifier} — skipping welcome message`, { accountId });
    return;
  }
  updateLeadStatus(accountId, identifier, "connected", { connectedAt: new Date().toISOString() });
  // Delay human-like: 2-8 minuti prima di mandare il messaggio (un umano non risponde in 5 secondi)
  const delay = humanRandom(120000, 480000);
  log("info", `Messaggio programmato tra ${Math.round(delay / 60000)} minuti per ${lead.name}`, { accountId });
  setTimeout(async () => {
    try {
      await sendWelcomeMessage(accountId, identifier, lead);
    } catch (error) {
      log("error", `Welcome message failed for ${identifier}: ${error.message}`, { accountId });
    }
  }, delay);
}

async function handleNewMessage(accountId, event) {
  const data = event.data || event;
  const senderId = data.sender_id || data.attendee_id || data.user_public_identifier;
  if (!senderId) return;
  const leads = getLeads(accountId);
  const lead = leads.find((l) => l.identifier === senderId);
  if (lead && lead.status === "messaged") {
    updateLeadStatus(accountId, senderId, "responded", {
      respondedAt: new Date().toISOString(),
      lastMessage: (data.text || data.message || "").substring(0, 200),
    });
    log("info", `Lead responded: ${lead.name}`, { accountId, identifier: senderId });
  }
}

function startServer() {
  const app = createWebhookServer();
  const port = config.webhook.port;
  app.listen(port, () => {
    log("info", `Webhook server running on port ${port}`);
    log("info", `Dashboard: http://localhost:${port}/dashboard`);
  });
  return app;
}

module.exports = { createWebhookServer, startServer };
