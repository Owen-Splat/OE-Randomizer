import zstandard
import oead

def zs_compress(data):
	return oead.yaz0.compress(data)

def zs_decompress(data):
	return oead.yaz0.decompress(data)


class SARC:
	def __init__(self, data: bytes, compressed=False):
		self.compressed = compressed
		if compressed:
			self.reader = oead.Sarc(zs_decompress(data))
		else:
			self.reader = oead.Sarc(data)
		self.writer = oead.SarcWriter.from_sarc(self.reader)
		oead.SarcWriter.set_endianness(self.writer, oead.Endianness.Little) # Switch uses Little Endian
	
	def repack(self):
		if self.compressed:
			return zs_compress(self.writer.write()[1])
		else:
			return self.writer.write()[1]


class BYAML:
	def __init__(self, data, compressed=False):
		self.compressed = compressed
		if self.compressed:
			data = oead.Bytes(zs_decompress(data))
		self.info = oead.byml.from_binary(data)

	def repack(self):
		data = oead.byml.to_binary(self.info, False, 3)
		if self.compressed:
			data = zs_compress(data)
		return data
