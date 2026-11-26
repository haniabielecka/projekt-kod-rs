from GF import GF

class Decoder:
    def __init__(self, gf: GF, t: int):
        self.gf = gf
        self.t = t
        self.n = gf.n
        self.k = gf.n - 2 * t
        self.g = gf.generate_generating_polynomial(t)

    # dekoder prosty
    def simple(self, wektor_odebrany: list[int]):
        wektor_odebrany = list(wektor_odebrany)
        wektor_skorygowany = list()
        g = self.g

        for i in range(0, self.k + 1):
            syndrom = self.gf.div_polynomials(wektor_odebrany, g)
            waga_syndromu = 0

            for el in syndrom:
                if el != self.gf.zero:
                    waga_syndromu += 1

            if waga_syndromu <= self.t:
                wektor_skorygowany = self.gf.add_polynomials(wektor_odebrany, syndrom)
                for _ in range(0, i):
                    wektor_skorygowany.append(wektor_skorygowany.pop(0))
                break
            else:
                if i == self.k:
                    return "Błędy niekorygowalne"
                else:
                    wektor_odebrany.insert(0, wektor_odebrany.pop())

        return wektor_skorygowany

    #  dekoder pełny
    def full(self, received: list[int]):
        zero = self.gf.zero
        syndromes = self.__calculate_syndromes(received)
        if all(s == zero for s in syndromes):
            return list(received)

        errors_location = self.__euclidean_algorythm(syndromes)
        positions = self.__chein_search(errors_location)

        if len(positions) == 0 or len(positions) != self.gf.degree(errors_location):
            return []
        if max(positions) >= len(received):
            return []

        y_tab = self.__error_values(syndromes, positions)

        e_x = [zero] * len(received)
        for pos, y in zip(positions, y_tab):
            e_x[len(received) - 1 - pos] = y
        c_x = self.gf.add_polynomials(received, e_x)

        if any(s != zero for s in self.__calculate_syndromes(c_x)):
            return []
        return c_x

    def __calculate_syndromes(self, received: list[int]) -> list[int]:
        return [self.gf.eval_polynomial(received, i) for i in range(1, 2 * self.t + 1)]

    def __euclidean_algorythm(self, syndromes: list[int]) -> list[int]:
        gf, t, zero = self.gf, self.t, self.gf.zero
        s_poly = gf.strip_polynomial(list(reversed(syndromes)))
        r_prev = [0] + [zero] * (2 * t)
        r_cur = s_poly
        t_prev = [zero]
        t_cur = [0]

        while gf.degree(r_cur) >= t:
            q, r_next = gf.divmod_polynomials(r_prev, r_cur)
            t_next = gf.add_polynomials(t_prev, gf.mul_polynomials(q, t_cur))
            r_prev, r_cur = r_cur, gf.strip_polynomial(r_next)
            t_prev, t_cur = t_cur, gf.strip_polynomial(t_next)
        return t_cur

    def __chein_search(self, sigma: list[int]) -> list[int]:
        positions = []
        for i in range(self.n):
            if self.gf.eval_polynomial(sigma, i) == self.gf.zero:
                positions.append((self.n - i) % self.n)
        return sorted(positions)

    def __error_values(self, syndromes: list[int], positions: list[int]) -> list[int]:
        gf, n, zero = self.gf, self.n, self.gf.zero
        T = len(positions)
        A = [[(i * p) % n for p in positions] + [syndromes[i - 1]] for i in range(1, T + 1)]

        for col in range(T):
            pivot = next((r for r in range(col, T) if A[r][col] != zero), None)
            if pivot is None:
                raise ValueError("Układ równań jest osobliwy")
            A[col], A[pivot] = A[pivot], A[col]
            pv = A[col][col]
            A[col] = [gf.div_alfa_powers(x, pv) for x in A[col]]
            for r in range(T):
                if r != col and A[r][col] != zero:
                    f = A[r][col]
                    A[r] = [gf.add_symbols(A[r][c], gf.add_alfa_powers(f, A[col][c]))
                            for c in range(T + 1)]
        return [A[i][T] for i in range(T)]