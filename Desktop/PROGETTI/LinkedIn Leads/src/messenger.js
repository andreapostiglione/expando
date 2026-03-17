const client = require("./unipile-client");
const { updateLeadStatus, getLeadsByStatus } = require("./store");
const { log, logMessage } = require("./logger");
const { getAccount } = require("./accounts");

// Backward-compat export — runtime code reads from account settings
const MESSAGE_TEMPLATES = {
  afterConnection: `{{MESSAGE_DA_PREPARARE}}`,
  followUp1: `{{FOLLOW_UP_1_DA_PREPARARE}}`,
  followUp2: `{{FOLLOW_UP_2_DA_PREPARARE}}`,
};

function personalizeMessage(template, lead) {
  const firstName = (lead.name || "").split(" ")[0] || "Ciao";
  return template
    .replace(/\{\{firstName\}\}/g, firstName)
    .replace(/\{\{name\}\}/g, lead.name || "")
    .replace(/\{\{headline\}\}/g, lead.headline || "")
    .replace(/\{\{company\}\}/g, lead.company || "");
}

async function sendWelcomeMessage(accountId, leadIdentifier, leadData = {}) {
  try {
    const settings = getAccount(accountId).settings;
    const template = settings.messageTemplates.afterConnection;

    if (!template || template.includes("DA_PREPARARE") || template.trim().length === 0) {
      log("warn", "Welcome message template not configured yet!", {
        identifier: leadIdentifier,
      });
      updateLeadStatus(accountId, leadIdentifier, "connected_awaiting_template");
      return { sent: false, reason: "template_not_configured" };
    }

    const message = personalizeMessage(template, leadData);

    log("info", `Sending welcome message to: ${leadData.name || leadIdentifier}`, {
      identifier: leadIdentifier,
    });

    // Start a new chat with the message
    const recipientId = leadData.providerId || leadIdentifier;
    const result = await client.startNewChat(accountId, recipientId, message);

    updateLeadStatus(accountId, leadIdentifier, "messaged", {
      messagedAt: new Date().toISOString(),
      chatId: result.chat_id,
    });

    logMessage({
      action: "welcome_sent",
      identifier: leadIdentifier,
      name: leadData.name,
      chatId: result.chat_id,
    });

    return { sent: true, chatId: result.chat_id };
  } catch (error) {
    log("error", `Failed to send message to: ${leadIdentifier}`, {
      error: error.message,
    });

    updateLeadStatus(accountId, leadIdentifier, "message_failed", {
      error: error.message,
    });

    return { sent: false, error: error.message };
  }
}

async function sendFollowUp(accountId, leadIdentifier, chatId, followUpNumber = 1) {
  try {
    const settings = getAccount(accountId).settings;
    const templateKey = `followUp${followUpNumber}`;
    const template = settings.messageTemplates[templateKey];

    if (!template || template.includes("DA_PREPARARE")) {
      log("warn", `Follow-up ${followUpNumber} template not configured`);
      return { sent: false, reason: "template_not_configured" };
    }

    const leads = getLeadsByStatus(accountId, "messaged");
    const lead = leads.find((l) => l.identifier === leadIdentifier);

    const message = personalizeMessage(template, lead || {});

    await client.sendMessageInChat(accountId, chatId, message);

    updateLeadStatus(accountId, leadIdentifier, "messaged", {
      [`followUp${followUpNumber}At`]: new Date().toISOString(),
      [`followUp${followUpNumber}Sent`]: true,
    });

    logMessage({
      action: `follow_up_${followUpNumber}_sent`,
      identifier: leadIdentifier,
      chatId,
    });

    return { sent: true };
  } catch (error) {
    log("error", `Follow-up ${followUpNumber} failed for: ${leadIdentifier}`, {
      error: error.message,
    });
    return { sent: false, error: error.message };
  }
}

module.exports = {
  sendWelcomeMessage,
  sendFollowUp,
  MESSAGE_TEMPLATES,
};
