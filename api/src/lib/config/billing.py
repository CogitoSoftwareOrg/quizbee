STRIPE_PRICES_MAP = {
    "plus_monthly": "price_1SGFmjPuRQMxFFQtexbkfz9X",
    "pro_monthly": "price_1SGFs0PuRQMxFFQtsBStJMnM",
    "plus_yearly": "price_1SGFnRPuRQMxFFQteWtWficS",
    "pro_yearly": "price_1SGFsPPuRQMxFFQtlJdds00h",
}

STRIPE_TARIFS_MAP = {
    "price_1SGFmjPuRQMxFFQtexbkfz9X": "plus",
    "price_1SGFnRPuRQMxFFQteWtWficS": "plus",
    "price_1SGFs0PuRQMxFFQtsBStJMnM": "pro",
    "price_1SGFsPPuRQMxFFQtlJdds00h": "pro",
}

STRIPE_MONTHLY_LIMITS_MAP = {
    "plus": {
        "quizItemsLimit": 1000,
        "messagesLimit": 1000,
        "bytesLimit": 8_388_608,  # 1GB
    },
    "pro": {
        "quizItemsLimit": 2000,
        "messagesLimit": 2000,
        "bytesLimit": 83_886_080,  # 100GB
    },
}
