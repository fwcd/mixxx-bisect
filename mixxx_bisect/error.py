class MixxxBisectError(Exception):
    pass

class UnsupportedArchError(MixxxBisectError):
    pass

class UnsupportedOSError(MixxxBisectError):
    pass

class EmptyRangeError(MixxxBisectError):
    pass

class NoCommitsFoundError(MixxxBisectError):
    pass

class MissingSnapshotsError(MixxxBisectError):
    pass
