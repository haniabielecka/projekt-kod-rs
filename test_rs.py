import random
import unittest

from GF import GF
from Encoder import Encoder
from Decoder import Decoder
from Transmitter import Transmitter

try:
    import reedsolo
except ImportError:
    reedsolo = None

T = 11

def corrupt(gf, word, positions):
    result = list(word)
    for p in positions:
        old = gf.alfas[result[p]]
        new = random.randrange(2 ** gf.m)
        while new == old:
            new = random.randrange(2 ** gf.m)
        result[p] = gf.find_alfa_power1(new)
    return result


def syndromes_zero(gf, word, t=T):
    return all(gf.eval_polynomial(word, i) == gf.zero for i in range(1, 2 * t + 1))


class BaseCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        random.seed(12345)
        cls.gf = GF(9)
        cls.enc = Encoder(cls.gf, T)
        cls.dec = Decoder(cls.gf, T)
        cls.n, cls.k = cls.gf.n, cls.enc.k

    def random_codeword(self):
        message = random.getrandbits(self.k * 9)
        return message, self.enc.encode(message)


class TestField(BaseCase):
    def test_alfas_are_distinct_and_cyclic(self):
        powers = self.gf.alfas[:self.n]
        self.assertEqual(len(set(powers)), self.n)
        self.assertNotIn(0, powers)
        self.assertEqual(self.gf.alfas[self.n], 1)
        self.assertEqual(self.gf.alfas[self.gf.zero], 0)

    def test_known_values_for_primitive_polynomial(self):
        # x^9 + x^4 + 1  =>  alfa^9 = alfa^4 + 1,  alfa^10 = alfa^5 + alfa
        self.assertEqual(self.gf.alfas[9], 0b000010001)
        self.assertEqual(self.gf.alfas[10], 0b000100010)

    def test_mul_div_inverse(self):
        for _ in range(500):
            a, b = random.randrange(self.n), random.randrange(self.n)
            prod = self.gf.add_alfa_powers(a, b)
            self.assertEqual(self.gf.div_alfa_powers(prod, b), a)
        self.assertEqual(self.gf.add_alfa_powers(self.gf.zero, 5), self.gf.zero)
        with self.assertRaises(ZeroDivisionError):
            self.gf.div_alfa_powers(3, self.gf.zero)

    def test_add_symbols_is_xor(self):
        for _ in range(500):
            a, b = random.randrange(self.n), random.randrange(self.n)
            expected = self.gf.find_alfa_power1(self.gf.alfas[a] ^ self.gf.alfas[b])
            self.assertEqual(self.gf.add_symbols(a, b), expected)
        self.assertEqual(self.gf.add_symbols(7, 7), self.gf.zero)   # a + a = 0

    def test_polynomial_example_from_report(self):
        self.assertEqual(self.gf.add_polynomials([9, 10, self.gf.zero], [4, 5, self.gf.zero]),
                         [0, 1, self.gf.zero])
        self.assertEqual(self.gf.mul_polynomials([300, self.gf.zero, self.gf.zero],
                                                 [250, self.gf.zero, self.gf.zero]),
                         [39] + [self.gf.zero] * 4)

    def test_divmod_identity(self):
        gf = self.gf
        for _ in range(30):
            a = [random.randrange(gf.n) for _ in range(random.randint(8, 40))]
            b = [random.randrange(gf.n) for _ in range(random.randint(2, 7))]
            q, r = gf.divmod_polynomials(a, b)
            lhs = gf.strip_polynomial(gf.add_polynomials(gf.mul_polynomials(q, b), r))
            self.assertEqual(lhs, gf.strip_polynomial(a))
            self.assertLess(gf.degree(r), gf.degree(b))

    def test_generating_polynomial(self):
        g = self.gf.generate_generating_polynomial(T)
        self.assertEqual(len(g), 2 * T + 1)
        self.assertEqual(g[0], 0)
        for i in range(1, 2 * T + 1):
            self.assertEqual(self.gf.eval_polynomial(g, i), self.gf.zero)
        self.assertNotEqual(self.gf.eval_polynomial(g, 2 * T + 1), self.gf.zero)


class TestEncoder(BaseCase):
    def test_report_example(self):
        enc2 = Encoder(self.gf, 2)
        self.assertEqual(self.gf.generate_generating_polynomial(2), [0, 391, 42, 396, 10])
        self.assertEqual(enc2.code_vector([3, 0, 7], 2), [3, 0, 7, 304, 141, 351, 32])

    def test_systematic_and_valid(self):
        for _ in range(5):
            message, cw = self.random_codeword()
            self.assertEqual(len(cw), self.n)
            self.assertEqual(cw[:self.k], self.enc.number_to_message(message))
            self.assertTrue(syndromes_zero(self.gf, cw))

    def test_number_roundtrip(self):
        for number in (0, 1, 511, 512, 2 ** 100 + 12345, random.getrandbits(self.k * 9)):
            self.assertEqual(self.enc.codeword_to_number(self.enc.encode(number)), number)

    def test_too_long_message_rejected(self):
        with self.assertRaises(ValueError):
            self.enc.encode(2 ** (self.k * 9))
        with self.assertRaises(ValueError):
            self.enc.encode(-1)

    def test_code_vector_does_not_modify_input(self):
        m = self.enc.number_to_message(12345)
        copy = list(m)
        self.enc.code_vector(m, T)
        self.assertEqual(m, copy)

    @unittest.skipIf(reedsolo is None, "brak biblioteki reedsolo (pip install reedsolo)")
    def test_matches_reference_library(self):
        rs = reedsolo.RSCodec(2 * T, nsize=self.n, fcr=1, prim=0x211, generator=2, c_exp=9)
        for _ in range(5):
            values = [random.randrange(512) for _ in range(self.k)]
            reference = list(rs.encode(values))
            message = [self.gf.find_alfa_power1(v) for v in values]
            ours = [self.gf.alfas[p] for p in self.enc.code_vector(message, T)]
            self.assertEqual(ours, reference)


class TestDecoders(BaseCase):
    def test_no_errors(self):
        _, cw = self.random_codeword()
        self.assertEqual(self.dec.full(cw), cw)
        self.assertEqual(self.dec.simple(cw), cw)

    def test_full_corrects_up_to_t_symbol_errors(self):
        for errors in range(1, T + 1):
            for _ in range(5):
                message, cw = self.random_codeword()
                rx = corrupt(self.gf, cw, random.sample(range(self.n), errors))
                fixed = self.dec.full(rx)
                self.assertEqual(fixed, cw, f"{errors} błędów")
                self.assertEqual(self.enc.codeword_to_number(fixed), message)

    def test_full_corrects_errors_in_parity_and_edges(self):
        _, cw = self.random_codeword()
        for positions in ([0], [self.n - 1], [0, self.n - 1], list(range(self.n - T, self.n)),
                          list(range(T))):
            self.assertEqual(self.dec.full(corrupt(self.gf, cw, positions)), cw, positions)

    def test_full_does_not_return_original_for_more_than_t_errors(self):
        _, cw = self.random_codeword()
        for _ in range(10):
            rx = corrupt(self.gf, cw, random.sample(range(self.n), T + 1))
            fixed = self.dec.full(rx)
            self.assertNotEqual(fixed, cw)
            if fixed:
                self.assertTrue(syndromes_zero(self.gf, fixed))

    def test_simple_corrects_errors_within_window_of_2t(self):
        for errors in (1, 5, T):
            for _ in range(3):
                _, cw = self.random_codeword()
                start = random.randrange(self.n)
                window = [(start + i) % self.n for i in range(2 * T)]
                rx = corrupt(self.gf, cw, random.sample(window, errors))
                self.assertEqual(self.dec.simple(rx), cw, f"{errors} błędów, start {start}")

    def test_simple_reports_uncorrectable_scattered_errors(self):
        _, cw = self.random_codeword()
        rx = corrupt(self.gf, cw, random.sample(range(self.n), T))
        result = self.dec.simple(rx)
        self.assertTrue(result == cw or result == "Błędy niekorygowalne")

    def test_both_correct_bursts_up_to_91_bits(self):
        for bits in (1, 9, 50, 91):
            for _ in range(3):
                _, cw = self.random_codeword()
                rx = Transmitter.burst(cw, bits)
                self.assertEqual(self.dec.full(rx), cw, f"full, burst {bits}")
                self.assertEqual(self.dec.simple(rx), cw, f"simple, burst {bits}")

    def test_decoders_do_not_modify_input(self):
        _, cw = self.random_codeword()
        rx = corrupt(self.gf, cw, [3, 4, 5])
        copy = list(rx)
        self.dec.simple(rx)
        self.dec.full(rx)
        self.assertEqual(rx, copy)

    @unittest.skipIf(reedsolo is None, "brak biblioteki reedsolo (pip install reedsolo)")
    def test_full_matches_reference_library(self):
        rs = reedsolo.RSCodec(2 * T, nsize=self.n, fcr=1, prim=0x211, generator=2, c_exp=9)
        _, cw = self.random_codeword()
        rx = corrupt(self.gf, cw, random.sample(range(self.n), T))
        reference = list(rs.decode([self.gf.alfas[p] for p in rx])[1])
        ours = [self.gf.alfas[p] for p in self.dec.full(rx)]
        self.assertEqual(ours, reference)


class TestTransmitter(BaseCase):
    def test_bit_stream_roundtrip(self):
        _, cw = self.random_codeword()
        stream = Transmitter.to_bit_stream(cw)
        self.assertEqual(len(stream), self.n * 9)
        self.assertEqual(Transmitter.from_bit_stream(stream), cw)

    @staticmethod
    def diff_positions(a, b):
        sa, sb = Transmitter.to_bit_stream(a), Transmitter.to_bit_stream(b)
        return [i for i in range(len(sa)) if sa[i] != sb[i]]

    def test_burst_flips_exactly_one_contiguous_run(self):
        _, cw = self.random_codeword()
        for bits in (1, 10, 99):
            diff = self.diff_positions(cw, Transmitter.burst(cw, bits))
            self.assertEqual(len(diff), bits)
            self.assertEqual(diff[-1] - diff[0] + 1, bits)

    def test_random_bits_flips_exact_number(self):
        _, cw = self.random_codeword()
        for bits in (1, 7, 40):
            self.assertEqual(len(self.diff_positions(cw, Transmitter.random_bits(cw, bits))), bits)

    def test_random_symbols_changes_at_most_given_number(self):
        _, cw = self.random_codeword()
        for count in (1, 5, 11):
            rx = Transmitter.random_symbols(cw, count)
            changed = sum(1 for a, b in zip(cw, rx) if a != b)
            self.assertLessEqual(changed, count)


if __name__ == "__main__":
    unittest.main(verbosity=2)