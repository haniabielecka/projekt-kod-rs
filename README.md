# Reed-Solomon RS(511,489) nad GF(2^9)

Własna implementacja kodera i dwóch dekoderów (prostego i pełnego) systematycznego kodu Reeda-Solomona w Pythonie. Projekt z przedmiotu *Niezawodność i diagnostyka układów cyfrowych 2*.

**Parametry:** `m = 9`, `t = 11`, `n = 511`, `k = 489`, wielomian pierwotny `x^9 + x^4 + 1`.

## Struktura projektu

| Plik | Opis |
|---|---|
| `GF.py` | ciało GF(2^9) i działania na wielomianach |
| `Encoder.py` | koder |
| `Decoder.py` | dekoder prosty (przesunięcia cykliczne) i pełny (Euklides, Chien) |
| `Transmitter.py` | symulacja kanału: błędy burstowe, na bitach i na symbolach |
| `test_rs.py` | testy jednostkowe |
| `experiments.py` | pomiary skuteczności i czasu dekodowania |
| `main.py` | krótki przykład użycia |
| `results/` | wyniki pomiarów (CSV, tabele LaTeX, wykresy) |


## Uruchomienie

Wymagany Python 3.9+.

```bash
pip install -r requirements.txt

python main.py                      # przykład: kodowanie, błędy, dekodowanie
python -m unittest test_rs -v       # testy
python experiments.py               # pomiary skuteczności (opcja --samples N)
python experiments.py --timing      # pomiar czasu dekodowania
```


## Autorzy

Hanna Bielecka, Maksym Tarasiuk
