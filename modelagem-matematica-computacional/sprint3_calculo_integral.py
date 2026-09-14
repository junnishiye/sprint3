# CHALLENGE SPRINT 3
# Modelagem Matemática e Computacional
# Cálculo Integral aplicado à Orquestração de Energia

# Integrantes:
# André — RM 571691
# Davi — RM 569487
# Gabriel — RM 568910
# Henrique — RM 570529
# João Vitor — RM 572079

import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

# 1. Definição das funções do enunciado
t = sp.symbols("t", real=True)
P1 = 5 + 20 * sp.sin(sp.pi * t / 24)
P2 = 16 + 15 * sp.cos(sp.pi * (t - 20) / 12)

print("FUNÇÕES DE POTÊNCIA")
print("P1(t) =", P1)
print("P2(t) =", P2)

# 2. Cálculo e exibição das antiderivadas
F1 = sp.integrate(P1, t)
F2 = sp.integrate(P2, t)

print("\nANTIDERIVADAS")
print("F1(t) =", F1)
print("F2(t) =", F2)

# 3. Resolução simbólica completa.
# A função exibe:
# integral definida -> antiderivada -> substituição dos limites
# -> F(b) -> F(a) -> resultado exato -> resultado decimal.
def resolver(nome, P, F, a, b):
    print("\n" + "=" * 72)
    print(nome)
    print("=" * 72)

    print("\n1) Integral definida:")
    sp.pprint(sp.Integral(P, (t, a, b)))

    print("\n2) Antiderivada:")
    sp.pprint(F)

    print("\n3) Substituição dos limites:")
    print(f"E = F({b}) - F({a})")

    Fb = sp.simplify(F.subs(t, b))
    Fa = sp.simplify(F.subs(t, a))

    print(f"\nF({b}) =")
    sp.pprint(Fb)
    print(f"\nF({a}) =")
    sp.pprint(Fa)

    resultado = sp.simplify(Fb - Fa)

    print("\n4) Resultado exato:")
    sp.pprint(resultado)

    print("\n5) Resultado aproximado:")
    print(f"E = {float(resultado.evalf()):.6f} kWh")

    return resultado

# 4. Exercício 1 — [0,24]
E1_P1 = resolver("EX. 1 — Posto 1 — [0,24] h", P1, F1, 0, 24)
E1_P2 = resolver("EX. 1 — Posto 2 — [0,24] h", P2, F2, 0, 24)

# 5. Exercício 2 — [0,6]
E2_P1 = resolver("EX. 2 — Posto 1 — [0,6] h", P1, F1, 0, 6)
E2_P2 = resolver("EX. 2 — Posto 2 — [0,6] h", P2, F2, 0, 6)

# 6. Exercício 3 — [10,16]
E3_P1 = resolver("EX. 3 — Posto 1 — [10,16] h", P1, F1, 10, 16)
E3_P2 = resolver("EX. 3 — Posto 2 — [10,16] h", P2, F2, 10, 16)

# 7. Exercício 4 — [18,24]
E4_P1 = resolver("EX. 4 — Posto 1 — [18,24] h", P1, F1, 18, 24)
E4_P2 = resolver("EX. 4 — Posto 2 — [18,24] h", P2, F2, 18, 24)

# 8. Gráfico das duas curvas no mesmo plano.
# As faixas dos Exercícios 2, 3 e 4 são destacadas.
# O Exercício 1 corresponde ao domínio completo [0,24].
x = np.linspace(0, 24, 1200)
y1 = 5 + 20 * np.sin(np.pi * x / 24)
y2 = 16 + 15 * np.cos(np.pi * (x - 20) / 12)

plt.figure(figsize=(12, 6.8))
plt.plot(x, y1, linewidth=2.6, label="Posto 1 — ChargeGrid Intelligence P1(t)")
plt.plot(x, y2, linewidth=2.6, label="Posto 2 — EV ChargeOps P2(t)")
plt.axvspan(0, 6, alpha=0.12, label="Ex. 2: 0–6 h")
plt.axvspan(10, 16, alpha=0.12, label="Ex. 3: 10–16 h")
plt.axvspan(18, 24, alpha=0.12, label="Ex. 4: 18–24 h")
plt.title("Curvas de potência dos dois postos ao longo de um dia")
plt.xlabel("Tempo t (horas)")
plt.ylabel("Potência P(t) (kW)")
plt.xlim(0, 24)
plt.ylim(0, 35)
plt.xticks(np.arange(0, 25, 2))
plt.grid(True, alpha=0.25)
plt.legend(loc="upper left", fontsize=9)
plt.tight_layout()
plt.show()
