# ==============================================================
# GLOBAL SOLUTION - MODELAGEM MATEMÁTICA COMPUTACIONAL
# Análise de Distribuição Normal e Regressão Linear
#
# Integrantes:
# André Balan Felix dos Santos - RM 571691
# Davi Sinhorini Pacheco - RM 569487
# Gabriel Da Silva Silveira - RM 568910
# Henrique De Souza Aragão - RM 570529
# João Vitor Jun Nishiye de Souza - RM 572079
#
# Turma: 1CCPQ
# ==============================================================

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# --------------------------------------------------------------
# 1. LEITURA E TRATAMENTO DA BASE
# --------------------------------------------------------------
PASTA = Path(__file__).resolve().parent
ARQUIVO = PASTA / "base_dados_limpa.csv"

if not ARQUIVO.exists():
    raise FileNotFoundError(
        f"Arquivo não encontrado: {ARQUIVO}\n"
        "Coloque 'base_dados_limpa.csv' na mesma pasta deste arquivo .py."
    )

df = pd.read_csv(ARQUIVO)
df.columns = df.columns.str.strip()

COLUNAS = ["MIN TEMP", "MAX TEMP", "MEAN TEMP"]
for coluna in COLUNAS:
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

# Remove valores ausentes e códigos inválidos de temperatura média.
df = df[df["MEAN TEMP"] > -90].dropna(subset=COLUNAS).copy()

if len(df) < 2:
    raise ValueError("A base não possui observações suficientes após o tratamento.")

temperatura = df["MEAN TEMP"]

# --------------------------------------------------------------
# 2. ESTATÍSTICA DESCRITIVA
# --------------------------------------------------------------
media = temperatura.mean()
mediana = temperatura.median()
desvio_padrao = temperatura.std(ddof=1)

print("=" * 70)
print("ANÁLISE ESTATÍSTICA - TEMPERATURA MÉDIA")
print("=" * 70)
print(f"Observações válidas: {len(df)}")
print(f"Média: {media:.4f} °F")
print(f"Mediana: {mediana:.4f} °F")
print(f"Desvio padrão amostral: {desvio_padrao:.4f} °F")

# --------------------------------------------------------------
# 3. ITEM 01 - PROBABILIDADE ACIMA DA MEDIANA
# --------------------------------------------------------------
# Hipótese solicitada no enunciado: a variável segue distribuição normal.
#
# Padronização:
# Z = (x - média) / desvio padrão
#
# Para P(X > mediana), usamos a função sobrevivência (sf):
# P(X > x) = 1 - F(x) = norm.sf(x, loc=média, scale=desvio padrão)

z_mediana = (mediana - media) / desvio_padrao
prob_acima_mediana = norm.sf(mediana, loc=media, scale=desvio_padrao)

print("\n" + "=" * 70)
print("01) PROBABILIDADE DE TEMPERATURA ACIMA DA MEDIANA")
print("=" * 70)
print(f"Mediana: {mediana:.4f} °F")
print(f"Z da mediana: {z_mediana:.4f}")
print(f"P(X > {mediana:.2f}) = {prob_acima_mediana:.4%}")
print("Classificação: pouco provável")

# --------------------------------------------------------------
# 4. ITEM 02 - PROBABILIDADE DENTRO DE MÉDIA ± 2s
# --------------------------------------------------------------
limite_inferior = media - 2 * desvio_padrao
limite_superior = media + 2 * desvio_padrao

prob_intervalo = (
    norm.cdf(limite_superior, loc=media, scale=desvio_padrao)
    - norm.cdf(limite_inferior, loc=media, scale=desvio_padrao)
)

print("\n" + "=" * 70)
print("02) PROBABILIDADE DENTRO DO INTERVALO MÉDIA ± 2s")
print("=" * 70)
print(f"Média: {media:.4f} °F")
print(f"Desvio padrão: {desvio_padrao:.4f} °F")
print(f"Limite inferior: {limite_inferior:.4f} °F")
print(f"Limite superior: {limite_superior:.4f} °F")
print(f"P({limite_inferior:.2f} <= X <= {limite_superior:.2f}) = {prob_intervalo:.4%}")
print("Classificação: quase certo")

# --------------------------------------------------------------
# 5. ITEM 03 - REGRESSÃO LINEAR
# --------------------------------------------------------------
# Variável explicativa (X): temperatura mínima
# Variável resposta (Y): temperatura média
#
# Modelo:
# Y = b0 + b1*X
#
# b0 = intercepto
# b1 = inclinação da reta

X = df[["MIN TEMP"]]
y = df["MEAN TEMP"]

modelo = LinearRegression()
modelo.fit(X, y)

intercepto = float(modelo.intercept_)
coeficiente = float(modelo.coef_[0])
previsoes = modelo.predict(X)
r2 = r2_score(y, previsoes)
correlacao = np.corrcoef(df["MIN TEMP"], y)[0, 1]

print("\n" + "=" * 70)
print("03) REGRESSÃO LINEAR")
print("=" * 70)
print("Variável X: Temperatura Mínima (°F)")
print("Variável Y: Temperatura Média (°F)")
print(f"Equação: Y = {intercepto:.4f} + {coeficiente:.4f}X")
print(f"Coeficiente angular (b1): {coeficiente:.4f}")
print(f"Intercepto (b0): {intercepto:.4f}")
print(f"Correlação de Pearson (r): {correlacao:.4f}")
print(f"Coeficiente de determinação (R²): {r2:.4f} ({r2:.2%})")

# --------------------------------------------------------------
# 6. GRÁFICOS
# --------------------------------------------------------------
x_grid = np.linspace(
    temperatura.min() - 4 * desvio_padrao,
    temperatura.max() + 4 * desvio_padrao,
    500
)

plt.figure(figsize=(9, 5))
plt.hist(temperatura, bins=20, density=True, alpha=0.65,
         label="Dados observados")
plt.plot(x_grid, norm.pdf(x_grid, media, desvio_padrao),
         linewidth=2, label="Normal ajustada")
plt.axvline(mediana, linestyle="--", linewidth=2,
            label=f"Mediana = {mediana:.2f} °F")
plt.title("Distribuição da Temperatura Média e Normal Ajustada")
plt.xlabel("Temperatura Média (°F)")
plt.ylabel("Densidade")
plt.legend()
plt.tight_layout()
plt.savefig(PASTA / "grafico_distribuicao_normal.png", dpi=180)
plt.show()

plt.figure(figsize=(9, 5))
plt.hist(temperatura, bins=20, density=True, alpha=0.65,
         label="Dados observados")
plt.plot(x_grid, norm.pdf(x_grid, media, desvio_padrao),
         linewidth=2, label="Distribuição Normal")
plt.axvspan(limite_inferior, limite_superior, alpha=0.22,
            label="Intervalo μ ± 2s")
plt.axvline(media, linestyle="--", linewidth=2,
            label=f"Média = {media:.2f} °F")
plt.title("Probabilidade dentro do intervalo Média ± 2s")
plt.xlabel("Temperatura Média (°F)")
plt.ylabel("Densidade")
plt.legend(fontsize=8)
plt.tight_layout()
plt.savefig(PASTA / "grafico_intervalo_2s.png", dpi=180)
plt.show()

plt.figure(figsize=(9, 5))
plt.scatter(df["MIN TEMP"], y, s=16, alpha=0.5,
            label="Observações")
xs = np.linspace(
    df["MIN TEMP"].min(),
    df["MIN TEMP"].max(),
    200
).reshape(-1, 1)
plt.plot(xs, modelo.predict(xs), linewidth=2,
         label="Reta de regressão linear")
plt.title("Regressão Linear: Temperatura Mínima × Temperatura Média")
plt.xlabel("Temperatura Mínima (°F)")
plt.ylabel("Temperatura Média (°F)")
plt.legend()
plt.tight_layout()
plt.savefig(PASTA / "grafico_regressao_linear.png", dpi=180)
plt.show()

# --------------------------------------------------------------
# 7. RESUMO FINAL
# --------------------------------------------------------------
print("\n" + "=" * 70)
print("RESUMO DOS RESULTADOS")
print("=" * 70)
print(f"01) P(X > mediana) = {prob_acima_mediana:.4%} -> pouco provável")
print(f"02) P(μ - 2s <= X <= μ + 2s) = {prob_intervalo:.4%} -> quase certo")
print(f"03) R² da regressão = {r2:.4f} -> relação linear muito forte")
print("=" * 70)
