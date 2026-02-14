class ArfException(Exception):
    pass


class RepoFetchError(ArfException):
    pass


class RPCError(ArfException):
    pass


class SrcinfoParseError(ArfException):
    def __init__(self, pkg, errors):
        self.pkg = pkg
        self.errors = errors
        super().__init__(f"SRCINFO for {pkg} is invalid")


class PackageResolutionError(ArfException):
    def __init__(self, pkg, parent=None):
        self.pkg = pkg
        self.parent = parent
        if parent:
            message = f"Failed to satisfy {pkg} required by {parent}"
        else:
            message = f"Package not found: {pkg}"
        super().__init__(message)
