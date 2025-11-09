STRIPE_PRICES_MAP = {
    "plus_monthly": "price_1SHi0fCrmGGYHLx7oHb9VCLF",
    "plus_yearly": "price_1SHhyyCrmGGYHLx7Z5iGCnEy",
    "pro_monthly": "price_1SHi3SCrmGGYHLx7TTE00Gau",
    "pro_yearly": "price_1SHi4BCrmGGYHLx7jx9QYOs7",
}

STRIPE_TARIFS_MAP = {
    "price_1SHi0fCrmGGYHLx7oHb9VCLF": "plus",
    "price_1SHhyyCrmGGYHLx7Z5iGCnEy": "plus",
    "price_1SHi3SCrmGGYHLx7TTE00Gau": "pro",
    "price_1SHi4BCrmGGYHLx7jx9QYOs7": "pro",
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
        "bytesLimit": 83_886_080,  # 10GB
    },
}
