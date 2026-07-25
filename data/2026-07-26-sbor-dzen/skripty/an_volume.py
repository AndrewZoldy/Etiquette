"""Гипотеза Андрея: рост числа публикаций — ОТВЕТ на падение, а не причина.
Проверяем порядок событий и каннибализацию внутри периодов."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 230)
pd.set_option("display.max_columns", 40)

art = pd.read_pickle("out/art.pkl")
rol = pd.read_pickle("out/rol.pkl")
pos = pd.read_pickle("out/pos.pkl")

all_pub = pd.concat([
    art.assign(kind="статья"), rol.assign(kind="ролик"), pos.assign(kind="пост")
])[["date", "ym", "kind", "shows", "opens", "reads", "title"]]

# ---------- 1. ПОРЯДОК СОБЫТИЙ: что раньше — рост объёма или спад ----------
print("=" * 140)
print("1. ПОРЯДОК СОБЫТИЙ. Медиана показов статьи vs объём публикаций, по месяцам")
t = pd.DataFrame({
    "статей": art.groupby("ym").size(),
    "мед_показы_статьи": art.groupby("ym")["shows"].median(),
    "всего_публикаций": all_pub.groupby("ym").size(),
}).loc["2025-01":"2026-07"]
t["статей_изм%"] = (t["статей"].pct_change() * 100).round(0)
t["показы_изм%"] = (t["мед_показы_статьи"].pct_change() * 100).round(0)
print(t.to_string())

# ---------- 2. КАННИБАЛИЗАЦИЯ ВНУТРИ ПЕРИОДА ----------
print("\n" + "=" * 140)
print("2. КАННИБАЛИЗАЦИЯ. Внутри одной эпохи: связана ли плотность публикаций с результатом статьи?")
art = art.sort_values("date").reset_index(drop=True)
# сколько ВСЕГО публикаций канала вышло в окне +-3 дня от этой статьи
apd = all_pub.sort_values("date").reset_index(drop=True)
dates = apd["date"].values.astype("datetime64[s]").astype(np.int64)


def density(ts, days=3):
    lo, hi = ts - days * 86400, ts + days * 86400
    return int(np.searchsorted(dates, hi) - np.searchsorted(dates, lo))


art["dens7"] = [density(int(pd.Timestamp(d).timestamp())) for d in art["date"]]
# дней с прошлой статьи
art["gap"] = art["date"].diff().dt.total_seconds().div(86400).round(1)

EPOCHS = [("до спада 2024-07..2025-07", "2024-07", "2025-07"),
          ("дно 2025-11..2026-07", "2025-11", "2026-07")]
for lbl, a, b in EPOCHS:
    d = art[(art.ym >= a) & (art.ym <= b)].copy()
    print(f"\n--- {lbl} (n={len(d)}) ---")
    d["dens_q"] = pd.qcut(d["dens7"], 3, labels=["редко", "средне", "часто"], duplicates="drop")
    g = d.groupby("dens_q", observed=True).agg(n=("shows", "size"),
                                               плотность=("dens7", "median"),
                                               мед_показы=("shows", "median"),
                                               мед_дочит=("reads", "median"),
                                               мед_ctr=("ctr", "median")).round(4)
    print(g.to_string())
    r = d[["dens7", "shows"]].corr(method="spearman").iloc[0, 1]
    rg = d.dropna(subset=["gap"])[["gap", "shows"]].corr(method="spearman").iloc[0, 1]
    print(f"Спирмен: плотность×показы = {r:+.3f} | пауза_с_прошлой×показы = {rg:+.3f}")

# ---------- 3. АРИФМЕТИКА: сколько объём может объяснить ----------
print("\n" + "=" * 140)
print("3. АРИФМЕТИКА. Может ли объём объяснить падение медианы?")
peak = art[(art.ym >= "2025-01") & (art.ym <= "2025-07")]
bot = art[(art.ym >= "2025-11") & (art.ym <= "2026-06")]
peak_all = all_pub[(all_pub.ym >= "2025-01") & (all_pub.ym <= "2025-07")]
bot_all = all_pub[(all_pub.ym >= "2025-11") & (all_pub.ym <= "2026-06")]
vol_k = (len(bot_all) / 8) / (len(peak_all) / 7)
med_k = peak.shows.median() / bot.shows.median()
sum_k = (peak.shows.sum() / 7) / (bot.shows.sum() / 8)
print(f"объём публикаций в месяц вырос в {vol_k:.2f} раза "
      f"({len(peak_all)/7:.0f} → {len(bot_all)/8:.0f} в месяц)")
print(f"медиана показов статьи упала в {med_k:.1f} раз")
print(f"суммарные показы статей в месяц упали в {sum_k:.1f} раз")
print(f"\nЕсли бы канал делил ФИКСИРОВАННЫЙ пирог между большим числом публикаций,")
print(f"медиана упала бы примерно в {vol_k:.1f} раза. Наблюдаем {med_k:.1f}.")
print(f"Необъяснённый остаток: {med_k/vol_k:.1f} раза — это сокращение самого пирога.")

# ---------- 4. Показы на публикацию всего канала ----------
print("\n" + "=" * 140)
print("4. ПИРОГ КАНАЛА: суммарные показы всех форматов в месяц")
pie = all_pub.groupby("ym").agg(публикаций=("shows", "size"), сумма_показов=("shows", "sum"))
pie["показов_на_публикацию"] = (pie["сумма_показов"] / pie["публикаций"]).round(0)
print(pie.loc["2025-01":"2026-07"].to_string())

# ---------- 5. Опережение/запаздывание ----------
print("\n" + "=" * 140)
print("5. ЛИД-ЛАГ: корреляция объёма месяца M с медианой показов месяца M+k")
s_vol = all_pub.groupby("ym").size().loc["2024-06":"2026-06"]
s_med = art.groupby("ym")["shows"].median().loc["2024-06":"2026-06"]
for k in (-3, -2, -1, 0, 1, 2, 3):
    a = s_vol.shift(k)
    df = pd.DataFrame({"v": a, "m": s_med}).dropna()
    if len(df) > 6:
        c = df.corr(method="spearman").iloc[0, 1]
        lbl = (f"объём опережает медиану на {k} мес" if k > 0
               else f"медиана опережает объём на {-k} мес" if k < 0 else "одновременно")
        print(f"  сдвиг {k:+d} ({lbl:38s}): rho={c:+.3f} (n={len(df)})")

art.to_pickle("out/art2.pkl")
