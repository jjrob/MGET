import importlib.metadata

try:
    __version__ = importlib.metadata.version("mget3")
except importlib.metadata.PackageNotFoundError:

    # If that failed, which should only happen during the build process, fall
    # back to extracting it from _version.py.

    try:
        import GeoEco._version
        __version__ = _version.__version__
    except:
        pass
