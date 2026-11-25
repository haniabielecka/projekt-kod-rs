PRIMITIVE_POLYNOMIAL = 0b1000010001

class GF:
    def __init__(self, m: int = 9, primitive_polynomial=PRIMITIVE_POLYNOMIAL ):
        self.m = m
        self.n = 2**m - 1
        self.zero = 2**m
        self.primitive_polynomial = primitive_polynomial
        self.alfas = self._create_alfas()
        self._log = {self.alfas[i]: i for i in range(self.n)}
        self._log[0] = self.zero

    # tworzenie symboli ciała
    def _create_alfas(self) -> list[int]:
        alfas = []
        value = 1
        for _ in range(self.n):
            alfas.append(value)
            value <<= 1
            if value & (1 << self.m):
                value ^= self.primitive_polynomial
        alfas.append(1)
        alfas.append(0)
        return alfas

    def pol_to_number(self, value) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value, 2)
        return int("".join(str(b) for b in value), 2)

    def find_alfa_power(self, value) -> int:
        return self._log[self.pol_to_number(value)]

    def find_alfa_power1(self, value: int) -> int:
        return self._log[value]

    # działania na symbolach
    def add_symbols(self, a: int, b: int) -> int:
        return self._log[self.alfas[a] ^ self.alfas[b]]

    def add_alfa_powers(self, a: int, b: int) -> int:
        if a == self.zero or b == self.zero:
            return self.zero
        return (a + b) % self.n

    def div_alfa_powers(self, a: int, b: int) -> int:
        if b == self.zero:
            raise ZeroDivisionError("Dzielenie przez zero w GF")
        if a == self.zero:
            return self.zero
        return (a - b) % self.n

    # wielomiany
    def strip_polynomial(self, p: list[int]) -> list[int]:
        i = 0
        while i < len(p) and p[i] == self.zero:
            i += 1
        return p[i:]

    def degree(self, p: list[int]) -> int:
        return len(self.strip_polynomial(p)) - 1 #wielomian z k wspólczynnikami ma stopień k-1

    def eval_polynomial(self, p: list[int], x: int) -> int:
        result = self.zero
        for c in p:
            result = self.add_symbols(self.add_alfa_powers(result, x), c)
        return result

    def add_polynomials(self, polynomial1: list[int], polynomial2: list[int]) -> list[int]:
        max_dlugosc = max(len(polynomial1), len(polynomial2))
        p1 = [self.zero] * (max_dlugosc - len(polynomial1)) + list(polynomial1)
        p2 = [self.zero] * (max_dlugosc - len(polynomial2)) + list(polynomial2)
        return [self.add_symbols(a, b) for a, b in zip(p1, p2)]

    def mul_polynomials(self, polynomial1: list[int], polynomial2: list[int]) -> list[int]:
        alfas, n, zero = self.alfas, self.n, self.zero
        wynik = [0] * (len(polynomial1) + len(polynomial2) - 1)
        for i, a in enumerate(polynomial1):
            if a == zero:
                continue
            for j, b in enumerate(polynomial2): #i pozycja w pierwszym wielomiane, a - wart. współczynnika
                if b == zero:
                    continue
                wynik[i + j] ^= alfas[(a + b) % n]
        return [self._log[v] for v in wynik]

    def divmod_polynomials(self, dividend: list[int], divisor: list[int]):
        alfas, log, n, zero = self.alfas, self._log, self.n, self.zero
        d = self.strip_polynomial(divisor)
        if not d:
            raise ZeroDivisionError("Dzielenie przez wielomian zerowy")
        dl = len(d)
        r = [alfas[x] for x in dividend]
        if len(r) < dl:
            return [zero], [zero] * (dl - 1 - len(r)) + [log[v] for v in r]
        d_nonzero = [(j, e) for j, e in enumerate(d) if e != zero]
        q = []
        for i in range(len(r) - dl + 1): #ilość cyfr ilorazu
            if r[i] == 0:
                q.append(zero)
                continue
            coef = (log[r[i]] - d[0]) % n   #dzielenie przez wiodący współczynnik dzielnika
            q.append(coef)
            for j, e in d_nonzero:
                r[i + j] ^= alfas[(e + coef) % n]
        reszta = r[len(r) - (dl - 1):]
        return q, [log[v] for v in reszta]

    def div_polynomials(self, dividend: list[int], divisor: list[int]) -> list[int]:
        return self.divmod_polynomials(dividend, divisor)[1]

    def generate_generating_polynomial(self, t: int) -> list[int]:
        generating_polynomial = [0, 1]
        for i in range(2, 2*t + 1):
            term = [0, i]  # (x + alpha^i)
            generating_polynomial = self.mul_polynomials(generating_polynomial, term)

        return generating_polynomial