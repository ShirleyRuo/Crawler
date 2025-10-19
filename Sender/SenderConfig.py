import hashlib

UPLOAD_FOLDER = r'.\Sender\uploads'
SPEED_TEST_FOLDER = r'.\Sender\speed_test'

class Config:

    def __init__(
            self,
            port: int = 5000,
            username: str = None,
            password: str = None,
        ) -> None:
        self.port = port
        self.username = username
        self.password = password
        self.upload_folder = UPLOAD_FOLDER
        self.speed_test_folder = SPEED_TEST_FOLDER

    @property
    def password(self):
        return self._password
    
    @password.setter
    def password(self, value):
        if not value:
            raise ValueError("密码不能为空")
        self._password = hashlib.sha256(value.encode('utf-8')).hexdigest()

sender_config = Config(
    port=5000,
    username='admin',
    password='123465'
)