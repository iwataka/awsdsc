class AwsdscException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnsupportedTypeException(AwsdscException):
    def __init__(self, typ: str):
        self.type = typ
        super().__init__(
            f"""Type "{typ}" is unsupported.
Run with --show-supported-types option for more details"""
        )
