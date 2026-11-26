import argparse
import csv
import os
import random
import time
from multiprocessing import Pool, cpu_count

from GF import GF
from Encoder import Encoder
from Decoder import Decoder
from Transmitter import Transmitter

T = 11
_enc = _dec = None


def _init_worker():
    global _enc, _dec
    gf = GF(9)
    _enc, _dec = Encoder(gf, T), Decoder(gf, T)


def _classify(result, cw, k):
    if isinstance(result, str) or len(result) == 0:
        return "detected"
    return "ok" if result[:k] == cw[:k] else "wrong"


def _run_task(task):
    kind, value, trials, seed = task
    random.seed(seed)
    counts = {f"{d}_{c}": 0 for d in ("full", "simple") for c in ("ok", "detected", "wrong")}
    for _ in range(trials):
        cw = _enc.encode(random.getrandbits(_enc.k * 9))
        if kind == "burst":
            rx = Transmitter.burst(cw, value)
        else:
            rx = Transmitter.random_symbols(cw, value)
        counts[f"full_{_classify(_dec.full(rx), cw, _enc.k)}"] += 1
        counts[f"simple_{_classify(_dec.simple(rx), cw, _enc.k)}"] += 1
    return kind, value, trials, counts


def run_measurements(kind, values, samples, workers, seed, chunk=25):
    tasks, task_seed = [], seed
    for v in values:
        left = samples
        while left > 0:
            n = min(chunk, left)
            tasks.append((kind, v, n, task_seed))
            task_seed += 1
            left -= n
    totals = {v: {"samples": 0} for v in values}
    started = time.time()
    with Pool(workers, initializer=_init_worker) as pool:
        for i, (_, v, n, counts) in enumerate(pool.imap_unordered(_run_task, tasks), 1):
            totals[v]["samples"] += n
            for key, c in counts.items():
                totals[v][key] = totals[v].get(key, 0) + c
            if i % 10 == 0 or i == len(tasks):
                print(f"[{kind}] {i}/{len(tasks)} zadań, {time.time() - started:.0f} s", flush=True)
    return totals


def pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def theory_burst(L):
    return 100.0 * min(max(100 - L, 0), 9) / 9


def write_csv(path, label, values, totals, with_theory=False):
    cols = ["samples"] + [f"{d}_{c}" for d in ("full", "simple") for c in ("ok", "detected", "wrong")]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([label] + cols + ["full_pct", "simple_pct"] + (["theory_pct"] if with_theory else []))
        for v in values:
            t = totals[v]
            row = [v] + [t.get(c, 0) for c in cols]
            row += [round(pct(t["full_ok"], t["samples"]), 2), round(pct(t["simple_ok"], t["samples"]), 2)]
            if with_theory:
                row.append(round(theory_burst(v), 2))
            w.writerow(row)


def fmt(x):
    return f"{x:.1f}".replace(".", ",") + r"\%"


def latex_tables(burst_vals, burst, sym_vals, sym):
    out = []
    out.append("% Tabela: błędy burstowe")
    out.append(r"\begin{table}[h]" + "\n" + r"\centering" + "\n" + r"\begin{tabular}{cccc}" + "\n" + r"\toprule")
    out.append(r"Długość wiązki [bity] & Teoria & Dekoder pełny & Dekoder prosty \\" + "\n" + r"\midrule")
    for v in burst_vals:
        t = burst[v]
        out.append(f"{v} & {fmt(theory_burst(v))} & {fmt(pct(t['full_ok'], t['samples']))} & "
                   f"{fmt(pct(t['simple_ok'], t['samples']))} \\\\")
    out.append(r"\bottomrule" + "\n" + r"\end{tabular}" + "\n" +
               r"\caption{Skuteczność dekodowania błędów burstowych.}" + "\n" +
               r"\label{tab:burst_results}" + "\n" + r"\end{table}" + "\n")
    out.append("% Tabela: błędy na symbolach")
    out.append(r"\begin{table}[h]" + "\n" + r"\centering" + "\n" + r"\begin{tabular}{ccc}" + "\n" + r"\toprule")
    out.append(r"Liczba błędnych symboli & Dekoder pełny & Dekoder prosty \\" + "\n" + r"\midrule")
    for v in sym_vals:
        t = sym[v]
        out.append(f"{v} & {fmt(pct(t['full_ok'], t['samples']))} & {fmt(pct(t['simple_ok'], t['samples']))} \\\\")
    out.append(r"\bottomrule" + "\n" + r"\end{tabular}" + "\n" +
               r"\caption{Skuteczność dekodowania błędów na symbolach.}" + "\n" +
               r"\label{tab:symbol_results}" + "\n" + r"\end{table}" + "\n")
    return "\n".join(out)


def make_plots(outdir, burst_vals, burst, sym_vals, sym):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Brak matplotlib - pomijam wykresy (pip install matplotlib).")
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(burst_vals, [pct(burst[v]["full_ok"], burst[v]["samples"]) for v in burst_vals], "o-", label="dekoder pełny")
    ax.plot(burst_vals, [pct(burst[v]["simple_ok"], burst[v]["samples"]) for v in burst_vals], "s--", label="dekoder prosty")
    ax.plot(burst_vals, [theory_burst(v) for v in burst_vals], ":", color="gray", label="teoria")
    ax.set_xlabel("Długość wiązki błędów [bity]"); ax.set_ylabel("Skuteczność [%]")
    ax.set_ylim(-3, 103); ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "burst.png"), dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(sym_vals, [pct(sym[v]["full_ok"], sym[v]["samples"]) for v in sym_vals], "o-", label="dekoder pełny")
    ax.plot(sym_vals, [pct(sym[v]["simple_ok"], sym[v]["samples"]) for v in sym_vals], "s--", label="dekoder prosty")
    ax.axvline(T + 0.5, color="gray", linestyle=":", label="$t = 11$")
    ax.set_xlabel("Liczba błędnych symboli"); ax.set_ylabel("Skuteczność [%]")
    ax.set_ylim(-3, 103); ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "symbols.png"), dpi=200); plt.close(fig)


def run_timing(outdir, repeats=20, seed=1):
    _init_worker()
    random.seed(seed)
    rows = []
    for errors in (0, 1, 5, 11):
        t_full = t_simple = 0.0
        for _ in range(repeats):
            cw = _enc.encode(random.getrandbits(_enc.k * 9))
            rx = Transmitter.random_symbols(cw, errors) if errors else list(cw)
            s = time.perf_counter(); _dec.full(rx); t_full += time.perf_counter() - s
            s = time.perf_counter(); _dec.simple(rx); t_simple += time.perf_counter() - s
        rows.append((errors, t_full / repeats, t_simple / repeats))
        print(f"{errors} błędów: pełny {rows[-1][1] * 1000:.1f} ms, prosty {rows[-1][2] * 1000:.1f} ms", flush=True)
    with open(os.path.join(outdir, "timing.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["errors", "full_s", "simple_s"]); w.writerows(rows)
    with open(os.path.join(outdir, "timing.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{table}[h]\n\\centering\n\\begin{tabular}{ccc}\n\\toprule\n"
                "Liczba błędnych symboli & Dekoder pełny [ms] & Dekoder prosty [ms] \\\\\n\\midrule\n")
        for e, a, b in rows:
            f.write(f"{e} & {a * 1000:.1f} & {b * 1000:.1f} \\\\\n".replace(".", ","))
        f.write("\\bottomrule\n\\end{tabular}\n\\caption{Średni czas dekodowania jednego słowa kodowego.}\n"
                "\\label{tab:timing}\n\\end{table}\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--samples", type=int, default=600, help="liczba prób na punkt pomiarowy")
    p.add_argument("--workers", type=int, default=0, help="liczba procesów (0 = wszystkie rdzenie)")
    p.add_argument("--burst-min", type=int, default=85)
    p.add_argument("--burst-max", type=int, default=105)
    p.add_argument("--symbols-max", type=int, default=15)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--out", default="results")
    p.add_argument("--timing", action="store_true", help="tylko pomiar czasu dekodowania")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.timing:
        run_timing(a.out)
        return
    workers = a.workers or cpu_count()
    burst_vals = list(range(a.burst_min, a.burst_max + 1))
    sym_vals = list(range(1, a.symbols_max + 1))
    burst = run_measurements("burst", burst_vals, a.samples, workers, a.seed)
    sym = run_measurements("symbols", sym_vals, a.samples, workers, a.seed + 100000)
    write_csv(os.path.join(a.out, "burst.csv"), "burst_bits", burst_vals, burst, with_theory=True)
    write_csv(os.path.join(a.out, "symbols.csv"), "symbols", sym_vals, sym)
    with open(os.path.join(a.out, "tables.tex"), "w", encoding="utf-8") as f:
        f.write(latex_tables(burst_vals, burst, sym_vals, sym))
    make_plots(a.out, burst_vals, burst, sym_vals, sym)
    print(f"Gotowe. Wyniki w folderze: {a.out}/")


if __name__ == "__main__":
    main()