import random

from GF import GF

class Transmitter:

    gf = GF(9)

    @staticmethod
    def to_bit_stream(data: list[int]) -> list[str]:
        return list("".join(format(Transmitter.gf.alfas[p], "09b") for p in data))

    @staticmethod
    def from_bit_stream(bin_stream: list[str]) -> list[int]:
        gf = Transmitter.gf
        reconstructing = [
            int("".join(bin_stream[i : i + 9]), 2) for i in range(0, len(bin_stream), 9)
        ]
        return [gf.find_alfa_power1(n) for n in reconstructing]

    @staticmethod
    def burst(
        data: list[int],
        bits_to_flip: int,
    ):

        gf = Transmitter.gf
        bin_stream = Transmitter.to_bit_stream(data)
        start_index = random.randint(0, len(bin_stream) - bits_to_flip - 1)

        while bits_to_flip > 0:
            if int(bin_stream[start_index]):
                bin_stream[start_index] = "0"
            else:
                bin_stream[start_index] = "1"
            bits_to_flip -= 1
            start_index += 1

        reconstructing = [
            int("".join(bin_stream[i : i + 9]), 2) for i in range(0, len(bin_stream), 9)
        ]

        polynomial = [gf.find_alfa_power1(n) for n in reconstructing]
        return polynomial

    @staticmethod
    def random_bits(data: list[int], bits_to_flip: int) -> list[int]:
        bin_stream = Transmitter.to_bit_stream(data)
        for idx in random.sample(range(len(bin_stream)), bits_to_flip):
            bin_stream[idx] = "0" if bin_stream[idx] == "1" else "1"
        return Transmitter.from_bit_stream(bin_stream)

    @staticmethod
    def random_symbols(data: list[int], symbols_to_change: int) -> list[int]:
        gf = Transmitter.gf
        result = list(data)
        for idx in random.sample(range(len(result)), symbols_to_change):
            result[idx] = gf.find_alfa_power1(random.randint(0, 2**gf.m - 1))
        return result