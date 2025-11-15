# Minimal stub: любые реальные обращения упадут с понятной ошибкой.
class _TorchStubError(ImportError):
    pass


def __getattr__(name):
    raise _TorchStubError(
        "This project uses a local stub for 'torch'. "
        "Install real PyTorch only if you actually need it."
    )
