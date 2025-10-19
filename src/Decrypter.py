from Crypto.Cipher import AES
from typing import Any, Optional
from EnumType import DecrptyType

class Decrypter:

    def __init__(
            self,
            decrpty_type : DecrptyType,
            **kwargs : Any
            ) -> None:
        self._decrypty_type = decrpty_type
    
    def decrypt(
            self,
            file_obj : Optional[bytes] = None,
            key : Optional[bytes] = None,
            iv : Optional[str] = None,
            **kwargs : Any
            ) -> bytes:
        if iv.startswith('0x'):
            iv = bytes.fromhex(iv[2:])
        else:
            iv = bytes.fromhex(iv)
        if self._decrypty_type == DecrptyType.AES:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(file_obj)
            return decrypted_data
        else:
            raise ValueError("不支持的解密类型")