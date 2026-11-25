from GF import GF

class Encoder:
    def __init__(self, gf: GF, t: int):
        self.gf = gf
        self.t = t
        self.n = gf.n
        self.k = gf.n - 2 * t

    def number_to_message(self, number: int, pad_to_k: bool = True) -> list[int]:
        if number < 0:
            raise ValueError("Informacja musi być nieujemną liczbą całkowitą")
        m = self.gf.m
        bits = bin(number)[2:]
        bits = bits.zfill(-(-len(bits) // m) * m)
        message = [self.gf.find_alfa_power(int(bits[i:i + m], 2))
                   for i in range(0, len(bits), m)]
        if len(message) > self.k:
            raise ValueError(f"Informacja nie mieści się w k = {self.k} symbolach")
        if pad_to_k:
            message = [self.gf.zero] * (self.k - len(message)) + message
        return message

    def code_vector(self, m: list[int], t: int):
        g = self.gf.generate_generating_polynomial(t)
        m = list(m) + [self.gf.zero] * (2*t)
        r = self.gf.div_polynomials(m, g)

        code_vec = self.gf.add_polynomials(m, r)

        return code_vec

    def encode(self, number: int) -> list[int]:
        return self.code_vector(self.number_to_message(number), self.t)

    def codeword_to_number(self, codeword: list[int]) -> int:
        m = self.gf.m
        bits = "".join(format(self.gf.alfas[p], f"0{m}b") for p in codeword[:self.k])
        return int(bits, 2)