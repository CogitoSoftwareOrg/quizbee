from nanoid import generate


def genID() -> str:
    return generate("abcdefghijklmnopqrstuvwxyz0123456789", 15)
