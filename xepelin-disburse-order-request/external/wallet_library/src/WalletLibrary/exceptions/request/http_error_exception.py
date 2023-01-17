class HttpErrorException(BaseException):
    def __init__(self, url, status):
        self.status = status

        super().__init__(f"Request to {url} failed with status {status}")
