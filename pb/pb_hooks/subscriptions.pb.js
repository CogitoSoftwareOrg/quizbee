/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  e.record.set("status", "active");
  e.record.set("tariff", "free");
  e.record.set("stripeInterval", "month");
  e.record.set("currentPeriodStart", new Date().toISOString());
  e.record.set(
    "currentPeriodEnd",
    new Date(
      Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() + 100, 1)
    ).toISOString()
  );
  // MONTHLY LIMITS FOR FREE USERS
  e.record.set("quizItemsLimit", 20);
  e.record.set("messagesLimit", 20);
  e.record.set("bytesLimit", 8_388_608);

  e.next();

  $app.runInTransaction((txApp) => {});
}, "subscriptions");

cronAdd("subscriptions_usage_reset_daily", "0 0 * * *", () => {
  function monthsDiff(a, b) {
    // a,b — Date в UTC; сколько полных месяц. от a до b
    return (
      (b.getUTCFullYear() - a.getUTCFullYear()) * 12 +
      (b.getUTCMonth() - a.getUTCMonth())
    );
  }

  function clampDay(year, month, day) {
    // вернёт безопасный день (например, anchor 31-е → в феврале станет 29/28)
    const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
    return Math.min(day, lastDay);
  }

  function monthWindowStartFromAnchor(
    anchorIso /* string ISO */,
    now /* Date */
  ) {
    if (!anchorIso) return null;
    const anchor = new Date(anchorIso); // ISO → UTC
    const m = monthsDiff(anchor, now);
    const day = anchor.getUTCDate();

    const base = new Date(
      Date.UTC(anchor.getUTCFullYear(), anchor.getUTCMonth(), 1)
    );
    const target = new Date(
      Date.UTC(base.getUTCFullYear(), base.getUTCMonth() + m, 1)
    );
    const d = clampDay(target.getUTCFullYear(), target.getUTCMonth(), day);
    return new Date(
      Date.UTC(target.getUTCFullYear(), target.getUTCMonth(), d, 0, 0, 0, 0)
    );
  }

  function computeWindowStart(sub, now) {
    const interval = sub.getString("stripeInterval"); // сохраняй из price.recurring.interval
    const cpStartIso = sub.getString("currentPeriodStart"); // уже есть у тебя
    if (!cpStartIso) return null;

    if (interval === "year") {
      // Внутренний месячный интервал от якоря годового периода
      return monthWindowStartFromAnchor(cpStartIso, now);
    }
    // Для monthly (и по умолчанию) — окно = начало текущего Stripe-периода
    return new Date(cpStartIso);
  }

  // RESET USAGE EVERY MONTH
  const now = new Date(); // UTC
  // только активные статусы
  const subs = $app.findRecordsByFilter(
    "subscriptions",
    "status = 'active' || status = 'trialing' || status = 'past_due'"
  );

  subs.forEach((s) => {
    const windowStart = computeWindowStart(s, now);
    const lastReset = s.getDateTime("lastUsageResetAt"); // Date или null

    if (!windowStart) return;

    // идемпотентность: сбрасываем, если ещё не сбрасывали для этого окна
    if (!lastReset || lastReset.getTime() < windowStart.getTime()) {
      s.set("lastUsageResetAt", now.toISOString());
      s.set("quizItemsUsage", 0);
      s.set("messagesUsage", 0);
      s.set("quizesUsage", 0);

      $app.save(s);
    }
  });
});
