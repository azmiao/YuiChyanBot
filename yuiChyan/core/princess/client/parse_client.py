from base64 import b64decode
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from msgpack import unpackb


class ParseClient:

    def __init__(self, udid, viewer_id, platform):
        self.viewer_id = viewer_id
        self.udid = udid
        self.platform = platform

    def _get_iv(self) -> bytes:
        return self.udid.replace('-', '')[:16].encode('utf8')

    def unpack(self, raw_data: bytes, key: Optional[bytes], aes: Optional):
        if not key:
            raw_data = b64decode(raw_data.decode('utf8'))
            key = raw_data[-32:]
            data = raw_data[:-32]
            aes = AES.new(key, AES.MODE_CBC, self._get_iv())
        else:
            data = raw_data
        dec = unpad(aes.decrypt(data), 16)
        return unpackb(dec, strict_map_key=False), key

    def parse_request(self, data: bytes, key: bytes):
        aes = AES.new(key, AES.MODE_CBC, self._get_iv())
        unpacked_data, key = self.unpack(data, key, aes)
        viewer_id_encrypted = b64decode(unpacked_data['viewer_id'])
        aes = AES.new(viewer_id_encrypted[-32:], AES.MODE_CBC, self._get_iv())
        viewer_id = unpad(aes.decrypt(viewer_id_encrypted[:-32]), 16).decode('utf8')
        unpacked_data['viewer_id'] = viewer_id
        return unpacked_data

    def parse_response(self, data: bytes):
        response, key = self.unpack(data, None, None)
        data_headers = response['data_headers']
        return response
