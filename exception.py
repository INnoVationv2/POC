class MyException(BaseException):
    def __init__(self, msg):
        self.error_msg = msg

    def __str__(self):
        return self.error_msg


class NifiException(MyException):
    pass


class NormalizeException(MyException):
    pass
