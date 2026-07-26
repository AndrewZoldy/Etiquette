import statistics as st

# date, words, showings, opens, reads, ctr, readthrough
rows = [
("18.05",1505,7607,238,86,0.0313,0.361),
("25.05",1808,5685,179,45,0.0315,0.251),
("01.06",1867,85887,907,218,0.0106,0.240),
("08.06",1551,144413,1674,382,0.0116,0.228),
("15.06",1627,56064,595,148,0.0106,0.249),
("22.06",2007,172640,2085,322,0.0121,0.154),
("29.06",2275,60259,520,117,0.0086,0.225),
("06.07",2392,71410,658,122,0.0092,0.185),
("13.07",2315,63774,493,77,0.0077,0.156),
("20.07",2742,29328,281,56,0.0096,0.199),
]

words=[r[1] for r in rows]; rt=[r[6] for r in rows]
print("median words", st.median(words), "median readthrough", st.median(rt))
print("median opens", st.median([r[3] for r in rows]), "median reads", st.median([r[4] for r in rows]))
print("median showings", st.median([r[2] for r in rows]), "median ctr", st.median([r[5] for r in rows]))

# Spearman
def rank(v):
    s=sorted(range(len(v)), key=lambda i:v[i])
    r=[0]*len(v)
    for pos,i in enumerate(s): r[i]=pos+1
    return r
rw=rank(words); rr=rank(rt)
n=len(words)
d2=sum((a-b)**2 for a,b in zip(rw,rr))
rho=1-6*d2/(n*(n*n-1))
print("spearman words vs readthrough rho=", round(rho,3))

# split medians (n=5 each -> below threshold, only for illustration)
print("first5 median words/rt", st.median(words[:5]), st.median(rt[:5]))
print("last5 median words/rt", st.median(words[5:]), st.median(rt[5:]))

# Nielsen model: time = 25 + 4.4 s per 100 words ; needed time at reading speed
def nielsen(w, wpm):
    t_avail = 25 + 0.044*w
    t_needed = w/wpm*60
    return t_avail, t_needed, t_avail/t_needed
for w in [1505,1867,2517,2742,592,111,917]:
    for wpm in (200,250):
        a,b,f = nielsen(w,wpm)
        print(f"words={w} wpm={wpm}: avail={a:.0f}s needed={b:.0f}s share={f*100:.1f}%")

print()
print("draft: words per event", 2517/41, "paragraphs", 2517/42)
print("draft reading time min @180/200/250 wpm", 2517/180, 2517/200, 2517/250)
print("111-word threshold ratio", 2517/111)
print("1250-word erratic threshold ratio", 2517/1250)
print("Medium 7min~1600 words ratio", 2517/1600)

# scenario math: to reach channel median reads 1136
showings = 63774
for rtx in (0.244, 0.35, 0.50, 0.53):
    opens_needed = 1136/rtx
    print(f"readthrough {rtx:.0%} -> opens needed {opens_needed:.0f}, CTR needed {opens_needed/showings*100:.2f}%")
# if only readthrough fixed, keep opens 595
for rtx in (0.244,0.35,0.50):
    print(f"opens 595 at readthrough {rtx:.0%} -> reads {595*rtx:.0f}")
# if only CTR fixed to channel 5.82%
opens = showings*0.0582
print("CTR 5.82% -> opens", round(opens), "reads at 24.4%:", round(opens*0.244), "at 50%:", round(opens*0.50))

# Iyengar jam ratio
print("jam: 6 opts 30% vs 24 opts 3% -> ratio", 30/3)
# 401k naive extrapolation
print("401k naive: 31 extra items x 0.175pp =", 31*0.175, "pp")
