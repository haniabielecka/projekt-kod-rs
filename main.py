import random
from GF import GF
from Encoder import Encoder
from Decoder import Decoder
from Transmitter import Transmitter

t = 11
gf = GF(9)
enc = Encoder(gf, t)
dec = Decoder(gf, t)

msg = random.getrandbits(489 * 9)
cw = enc.encode(msg)

rx = Transmitter.random_symbols(cw, 5)
print("full ok:", dec.full(rx) == cw)
print("simple ok:", dec.simple(rx) == cw)