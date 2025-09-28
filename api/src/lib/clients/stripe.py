import stripe

from src.lib.settings import settings

stripe.api_key = settings.stripe_api_key
