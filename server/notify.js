// Telegram notifications for new orders/leads. Fully optional — if the env
// vars below aren't set, this silently no-ops (server still works, you just
// have to check /admin.html yourself). Setup: docs/launch-checklist.md.

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const CHAT_ID = process.env.TELEGRAM_CHAT_ID;

let warnedOnce = false;

async function sendTelegramMessage(text) {
  if (!BOT_TOKEN || !CHAT_ID) {
    if (!warnedOnce) {
      console.warn(
        'Telegram notifications disabled: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable (see docs/launch-checklist.md).'
      );
      warnedOnce = true;
    }
    return;
  }
  try {
    const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: CHAT_ID, text, parse_mode: 'HTML' }),
    });
    if (!res.ok) {
      console.error('Telegram notify failed:', res.status, await res.text());
    }
  } catch (err) {
    console.error('Telegram notify error:', err.message);
  }
}

function notifyNewOrder(order) {
  const itemsText = order.items
    .map((i) => `• ${i.name} — ${i.qty} шт (${i.color || '—'}, ${i.size || '—'})`)
    .join('\n');
  const text =
    `🆕 <b>Новая заявка №${order.id}</b>\n` +
    `Компания: ${order.company}\n` +
    `Контакт: ${order.contactName}, ${order.phone}${order.email ? `, ${order.email}` : ''}\n` +
    `Сумма: ${order.total.toLocaleString('ru-RU')} ₽\n\n` +
    `${itemsText}` +
    (order.comment ? `\n\nКомментарий: ${order.comment}` : '');
  return sendTelegramMessage(text);
}

function notifyNewLead(lead) {
  const text =
    `📩 <b>Новое обращение №${lead.id}</b>\n` +
    `${lead.name}${lead.phone ? `, ${lead.phone}` : ''}${lead.email ? `, ${lead.email}` : ''}` +
    (lead.message ? `\n\n${lead.message}` : '');
  return sendTelegramMessage(text);
}

module.exports = { notifyNewOrder, notifyNewLead };
