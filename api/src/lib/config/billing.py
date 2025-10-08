STRIPE_PRICES_MAP = {
    "plus_monthly": "price_1SCFmCPuRQMxFFQtHOEmHUWv",
    "pro_monthly": "price_1SCG2hPuRQMxFFQtaYLDDgDp",
    "plus_yearly": "price_1SCFnmPuRQMxFFQtwZF7VUHz",
    "pro_yearly": "price_1SCG4pPuRQMxFFQtMZ0bhmYW",
}

STRIPE_TARIFS_MAP = {
    "price_1SCFmCPuRQMxFFQtHOEmHUWv": "plus",
    "price_1SCFnmPuRQMxFFQtwZF7VUHz": "plus",
    "price_1SCG2hPuRQMxFFQtaYLDDgDp": "pro",
    "price_1SCG4pPuRQMxFFQtMZ0bhmYW": "pro",
}

STRIPE_MONTHLY_LIMITS_MAP = {
    "plus": {
        "quizItemsLimit": 400,
        "messagesLimit": 400,
        "bytesLimit": 8_388_608,  # 1GB
    },
    "pro": {
        "quizItemsLimit": 1000,
        "messagesLimit": 1000,
        "bytesLimit": 83_886_080,  # 100GB
    },
}
