#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChargeGrid Intelligence — Sprint 3
Integração independente Arduino + 74HC/Tinkercad + Python.

Modos:
  --demo        executa 5 cenários de demonstração
  --self-test   verifica as 32 combinações booleanas
  --truth-table imprime tabela verdade compacta
  --serial COM3 lê telemetria real do Arduino

Protocolo:
CG,AUTH,VAGA,ENERGIA,S_SESSAO,PRIORIDADE,P_74HC,FINAL,ENERGIA_PCT
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from itertools import product
from pathlib import Path

try:
    import serial
except ImportError:
    serial = None


def sessao_logic(auth: int, vaga: int, energia: int) -> int:
    """S_sessao = (AUTH AND VAGA) OR (VAGA AND ENERGIA)."""
    return int(bool((auth and vaga) or (vaga and energia)))


def final_logic(s_sessao: int, prioridade: int, p_74hc: int) -> int:
    """FINAL = S_sessao AND (NOT PRIORIDADE OR P_74HC)."""
    return int(bool(s_sessao and ((not prioridade) or p_74hc)))


def energia_logic(energia_pct: int) -> int:
    """Energia suficiente quando o percentual normalizado >= 50%."""
    return int(energia_pct >= 50)


def controle(final_ok: int, energia_pct: int) -> tuple[str, float]:
    """Converte a decisão lógica em um estado/potência de referência."""
    limite_kw = 22.0

    if not final_ok:
        return "BLOQUEADA", 0.0
    if energia_pct < 50:
        return "LIMITADA", 11.0
    return "AUTORIZADA", limite_kw


def _parse_ints(parts: list[str]) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in parts)
    except ValueError as exc:
        raise ValueError("há um campo que não é inteiro") from exc


def parse(line: str) -> dict | None:
    parts = line.strip().split(",")

    if parts[0] != "CG":
        return None

    if len(parts) != 9:
        raise ValueError(
            f"quantidade de campos inválida: esperado 9, recebido {len(parts)}"
        )

    (
        auth,
        vaga,
        energia,
        s_sessao_arduino,
        prioridade,
        p74hc,
        final_arduino,
        energia_pct,
    ) = _parse_ints(parts[1:])

    bool_fields = {
        "AUTH": auth,
        "VAGA": vaga,
        "ENERGIA": energia,
        "S_SESSAO": s_sessao_arduino,
        "PRIORIDADE": prioridade,
        "P_74HC": p74hc,
        "FINAL": final_arduino,
    }

    invalid = [name for name, value in bool_fields.items() if value not in (0, 1)]
    if invalid:
        raise ValueError(
            "campos booleanos fora de {0,1}: " + ", ".join(invalid)
        )

    if not 0 <= energia_pct <= 100:
        raise ValueError("ENERGIA_PCT deve estar entre 0 e 100")

    s_calc = sessao_logic(auth, vaga, energia)
    energia_calc = energia_logic(energia_pct)
    final_calc = final_logic(s_calc, prioridade, p74hc)

    consistencia = (
        s_sessao_arduino == s_calc
        and final_arduino == final_calc
        and energia == energia_calc
    )

    status, potencia = controle(final_calc, energia_pct)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "auth": auth,
        "vaga": vaga,
        "energia_arduino": energia,
        "energia_python": energia_calc,
        "s_sessao_arduino": s_sessao_arduino,
        "s_sessao_python": s_calc,
        "prioridade": prioridade,
        "p_74hc": p74hc,
        "final_arduino": final_arduino,
        "final_python": final_calc,
        "energia_pct": energia_pct,
        "status": status,
        "potencia_kw": potencia,
        "consistencia": "OK" if consistencia else "DIVERGENTE",
    }


def show(result: dict) -> None:
    print("\n" + "=" * 76)
    print("CHARGEGRID — INTEGRAÇÃO SPRINT 3")
    print("=" * 76)
    print(
        f"AUTH={result['auth']} | VAGA={result['vaga']} | "
        f"ENERGIA Arduino={result['energia_arduino']} | "
        f"ENERGIA Python={result['energia_python']}"
    )
    print(
        f"PRIORIDADE={result['prioridade']} | "
        f"P74HC={result['p_74hc']} | "
        f"ENERGIA_PCT={result['energia_pct']}%"
    )
    print(
        f"S_SESSAO: Arduino={result['s_sessao_arduino']} | "
        f"Python={result['s_sessao_python']}"
    )
    print(
        f"FINAL: Arduino={result['final_arduino']} | "
        f"Python={result['final_python']}"
    )
    print(f"Status calculado pelo Python: {result['status']}")
    print(f"Potência de referência: {result['potencia_kw']:.1f} kW")
    print(f"Consistência: {result['consistencia']}")
    print("=" * 76)


def demo() -> list[dict]:
    scenarios = [
        ("1 - Sessão normal", "CG,1,1,1,1,0,0,1,85"),
        ("2 - Energia baixa", "CG,1,1,0,1,0,0,1,35"),
        ("3 - Sem vaga", "CG,1,0,1,0,0,0,0,90"),
        ("4 - Prioridade liberada", "CG,1,1,1,1,1,1,1,85"),
        ("5 - Prioridade bloqueada", "CG,1,1,1,1,1,0,0,85"),
    ]

    rows: list[dict] = []

    for name, line in scenarios:
        print(f"\n>>> {name}")
        try:
            result = parse(line)
        except ValueError as exc:
            print("[ERRO]", exc)
            continue

        if result is not None:
            rows.append(result)
            show(result)

    return rows


def all_combinations() -> list[dict]:
    rows = []

    for auth, vaga, energia, prioridade, p74hc in product((0, 1), repeat=5):
        s = sessao_logic(auth, vaga, energia)
        final = final_logic(s, prioridade, p74hc)

        rows.append({
            "AUTH": auth,
            "VAGA": vaga,
            "ENERGIA": energia,
            "PRIORIDADE": prioridade,
            "P_74HC": p74hc,
            "S_SESSAO": s,
            "FINAL": final,
        })

    return rows


def self_test() -> None:
    rows = all_combinations()

    for row in rows:
        expected_s = sessao_logic(row["AUTH"], row["VAGA"], row["ENERGIA"])
        expected_final = final_logic(
            row["S_SESSAO"], row["PRIORIDADE"], row["P_74HC"]
        )

        assert row["S_SESSAO"] == expected_s
        assert row["FINAL"] == expected_final

    assert energia_logic(49) == 0
    assert energia_logic(50) == 1
    assert energia_logic(100) == 1
    assert energia_logic(0) == 0

    print(f"SELF-TEST OK: {len(rows)} combinações verificadas.")
    print("Limiar de energia: 49% -> 0 | 50% -> 1")


def print_truth_table() -> None:
    print("\nAUTH VAGA ENERGIA PRIORIDADE | S_SESSAO | FINAL(P=0) FINAL(P=1)")
    print("-" * 66)

    for auth, vaga, energia, prioridade in product((0, 1), repeat=4):
        s = sessao_logic(auth, vaga, energia)
        f0 = final_logic(s, prioridade, 0)
        f1 = final_logic(s, prioridade, 1)

        print(
            f"  {auth}    {vaga}      {energia}         {prioridade}"
            f"      |    {s}     |      {f0}          {f1}"
        )


def save(rows: list[dict], path: Path) -> None:
    if not rows:
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def serial_loop(port: str, baud: int) -> list[dict]:
    if serial is None:
        raise RuntimeError(
            "PySerial não está instalado. Execute: "
            "pip install -r python/requirements.txt"
        )

    rows: list[dict] = []
    print(f"Lendo {port} a {baud} baud. Ctrl+C para encerrar.")

    try:
        with serial.Serial(
            port=port,
            baudrate=baud,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        ) as ser:
            while True:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="replace").strip()

                try:
                    result = parse(line)
                except ValueError as exc:
                    print("[LINHA INVÁLIDA]", line)
                    print("[MOTIVO]", exc)
                    continue

                if result is None:
                    continue

                rows.append(result)
                show(result)

    except KeyboardInterrupt:
        print("\nLeitura serial encerrada.")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ChargeGrid Intelligence — Sprint 3"
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--truth-table", action="store_true")
    mode.add_argument("--serial", metavar="PORTA")

    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument(
        "--saida",
        default="python/resultados_sprint3.csv",
        help="arquivo CSV de saída",
    )

    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    if args.truth_table:
        print_truth_table()
        return

    if args.serial:
        rows = serial_loop(args.serial, args.baud)
        save(rows, Path(args.saida))
        print(f"\nCSV salvo em: {args.saida}")
        return

    rows = demo()
    save(rows, Path(args.saida))
    print(f"\nCSV salvo em: {args.saida}")


if __name__ == "__main__":
    main()
