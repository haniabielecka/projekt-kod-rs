# Reed-Solomon RS(511,489) nad GF(2^9)

Własna implementacja kodera i dwóch dekoderów (prostego i pełnego) systematycznego kodu Reeda-Solomona w Pythonie. Projekt z przedmiotu *Niezawodność i diagnostyka układów cyfrowych 2*.

**Parametry:** `m = 9`, `t = 11`, `n = 511`, `k = 489`, wielomian pierwotny `x^9 + x^4 + 1`.

## Struktura projektu

| Plik | Opis |
|---|---|
| `GF.py` | ciało GF(2^9) i działania na wielomianach |
| `Encoder.py` | koder |
| `Transmitter.py` | symulacja kanału: błędy burstowe, na bitach i na symbolach |


## Autorzy

Hanna Bielecka, Maksym Tarasiuk
