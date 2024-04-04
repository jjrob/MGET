import importlib.metadata

try:
    __version__ = importlib.metadata.version("mget3")
except importlib.metadata.PackageNotFoundError:
    pass
