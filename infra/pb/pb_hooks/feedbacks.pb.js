/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation

  e.next();

  const user = e.record.get("user");
  const content = e.record.get("content");
  const type = e.record.get("type");
  const rating = e.record.get("rating");
  const metadata = e.record.get("metadata");

  const tg = require(`${__hooks}/lib/tg.js`).tgService;

  // Format the message beautifully
  const ratingEmoji = rating >= 4 ? "⭐" : rating >= 3 ? "👍" : "👎";
  const typeEmoji = type === "bug" ? "🐛" : type === "feature" ? "💡" : "💬";

  const message = `
🆕 <b>Новый отзыв получен!</b>

${typeEmoji} <b>Тип:</b> <code>${type}</code>
${ratingEmoji} <b>Оценка:</b> <code>${rating}/5</code>
👤 <b>Пользователь:</b> <code>${user}</code>

💬 <b>Сообщение:</b>
<i>${content}</i>

${
  metadata
    ? `📋 <b>Метаданные:</b> <code>${JSON.stringify(metadata)}</code>`
    : ""
}
━━━━━━━━━━━━━━━━━━━━━━
  `.trim();

  tg.send(message);
}, "feedbacks");
