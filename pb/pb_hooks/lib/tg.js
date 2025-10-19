const tgService = {
  init() {
    this.token = $os.getenv("TG_TOKEN");
    this.chatId = $os.getenv("TG_ID");
  },
  send(message) {
    try {
      const res = $http.send({
        url: `https://api.telegram.org/bot${this.token}/sendMessage`,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          chat_id: this.chatId,
          text: message,
          parse_mode: "HTML",
        }),
      });

      if (res.statusCode !== 200) {
        console.error("Telegram API error:", res.statusCode, res.raw);
      }
    } catch (error) {
      console.error("Failed to send Telegram message:", error);
    }
  },
};

module.exports = {
  tgService,
};
