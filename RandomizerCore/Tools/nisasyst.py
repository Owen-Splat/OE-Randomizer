# modified from SciresM's script found here
# https://gist.github.com/SciresM/dba70bc2ee7eca11e1bd777ecb58ff16

import zlib
from Crypto.Cipher import AES

def u32(x):
    return (x & 0xFFFFFFFF)

KEY_MATERIAL = 'e413645fa69cafe34a76192843e48cbd691d1f9fba87e8a23d40e02ce13b0d534d10301576f31bc70b763a60cf07149cfca50e2a6b3955b98f26ca84a5844a8aeca7318f8d7dba406af4e45c4806fa4d7b736d51cceaaf0e96f657bb3a8af9b175d51b9bddc1ed475677260f33c41ddbc1ee30b46c4df1b24a25cf7cb6019794'

class sead_rand:
    """Implements Splatoon 2's mersenne random generator"""

    def __init__(self, seed):
        self.seed = u32(seed)
        self.state = [self.seed]
        for i in range(1, 5):
            self.state.append(u32(0x6C078965 * (self.state[-1] ^ (self.state[-1] >> 30)) + i))
        self.state = self.state[1:]

    def get_u32(self):
        a = u32(self.state[0] ^ (self.state[0] << 11))
        self.state[0] = self.state[1]
        b = u32(self.state[3])
        c = u32(a ^ (a >> 8) ^ b ^ (b >> 19))
        self.state[1] = self.state[2]
        self.state[2] = b
        self.state[3] = c
        return c


class NisasystContainer:
    def __init__(self, fn, data):
        if data[-8:] != b'nisasyst':
            raise ValueError('Error: Input appears not to be an encrypted Splatoon 2 archive!')
        seed = u32(zlib.crc32(bytes(fn, 'utf-8')))
        key_iv = ''
        rnd = sead_rand(seed)
        for _ in range(0x40):
            key_iv += KEY_MATERIAL[(rnd.get_u32() >> 24)]
        key_iv = bytes.fromhex(key_iv)
        self.key, self.iv = key_iv[:0x10], key_iv[0x10:]
        self.data = AES.new(self.key, AES.MODE_CBC, self.iv).decrypt(data[:-8])

    def repack(self):
        while (len(self.data) % 16) != 0:
            self.data += b'\x00'
        result = AES.new(self.key, AES.MODE_CBC, self.iv).encrypt(self.data)
        result += b'nisasyst'
        return result
