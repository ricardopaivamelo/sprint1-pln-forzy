# Sprint 1 — Processamento de Linguagem Natural | Digital Twin de Motores Elétricos

Sprint 1 da disciplina **FIAP — PLN** (Challenge **Forzy**). Corpus textual base do digital twin de motores elétricos industriais, com glossário PT/EN e pipeline de pré-processamento reproduzível.

## Grupo

| Nome | RM |
|---|---|
| Nicolas Lemos Ribeiro | 553273 |
| Ricardo de Paiva Melo | 565522 |
| Luís Fernando de Oliveira Salgado | 561401 |
| Pedro Leal Murad | 565460 |
| Murilo Benhossi | 562358 |
| Jonas Alaf | 566479 |

---

## Entregáveis cumpridos

| # | Entregável | Artefato | Status |
|---|------------|----------|--------|
| 1 | Inventário e Padronização Terminológica | `data/reference/glossario_motores.json` (v1.1) | ✅ 110 termos PT/EN em 8 categorias + 9 fabricantes padronizados (com variações) + 30 sinônimos + 40+ abreviações |
| 2 | Pipeline de Pré-processamento Textual | `src/preprocessing.py` + notebook | ✅ Tokenização customizada, expansão de abreviações, **normalização de unidades**, **normalização de fabricantes**, stopwords técnicas, lematização (simplemma) + 2 stemmings (RSLP, Snowball) em paralelo |
| 3 | Corpus Estruturado e Documentado | `data/processed/corpus_processed.jsonl` + `corpus_metadata.csv` + `corpus_stats.json` + **`decisoes_padronizacao.json`** | ✅ 100 docs com metadados completos + 9 decisões metodológicas documentadas |

**Métricas-chave (atendem o brief):**
- **Comparação 3-way de redução morfológica** (cobertura do glossário pós-processamento):
  - Lematização (simplemma): **16,97%**
  - Stemming Snowball: **10,30%**
  - Stemming RSLP: **7,58%**
- Lematização preserva **2,24× mais terminologia que RSLP** e **1,65× mais que Snowball**.
- **Normalização de fabricantes:** 100% dos documentos com variantes (12/100) corretamente normalizados.

## Estrutura

```
sprint1-nlp-motores/
├── README.md
├── requirements.txt
├── docs/
│   ├── briefing/sprintNLP.txt          brief original FIAP
│   └── planning/
│       ├── ANALYSIS.md                  análise técnica do brief
│       └── QUESTIONS.md                 perguntas abertas (registro histórico)
├── notebooks/
│   └── sprint1_pln_corpus.ipynb         entregável oficial (rodável end-to-end)
├── data/
│   ├── raw/corpus_raw.jsonl             100 docs sintéticos (seed=42, reproduzível)
│   ├── processed/
│   │   ├── corpus_processed.jsonl       corpus normalizado (tokens, lemmas, stems_rslp, stems_snowball)
│   │   ├── corpus_metadata.csv          metadados achatados em CSV
│   │   ├── corpus_stats.json            estatísticas + comparação 3-way (lema × RSLP × Snowball)
│   │   └── decisoes_padronizacao.json   9 decisões metodológicas estruturadas
│   └── reference/glossario_motores.json glossário PT/EN v1.1 (termos + sinônimos + fabricantes)
└── src/
    ├── synthetic_corpus_generator.py    gera corpus sintético reproduzível
    ├── preprocessing.py                 pipeline completo (tokenize→lemma+stem)
    └── corpus_stats.py                  métricas + comparação metodológica
```

## Setup

```bash
# Python 3.11+ recomendado
pip install -r requirements.txt
```

## Reproduzir o pipeline

```bash
# 1. Gerar corpus sintético (100 docs, seed=42)
python src/synthetic_corpus_generator.py

# 2. Pré-processar (tokenização, lema, stem, idioma)
python src/preprocessing.py

# 3. Estatísticas + comparação lema/stem
python src/corpus_stats.py

# 4. Ou rodar tudo via notebook (entrega oficial)
jupyter notebook notebooks/sprint1_pln_corpus.ipynb
```

Reprodutibilidade: seed fixada em `42`, dependências pinadas em `requirements.txt`.

## Decisões metodológicas

9 decisões documentadas em `data/processed/decisoes_padronizacao.json` (estrutura: tema, decisão, justificativa, evidência empírica, impacto). Resumo:

1. **D001 — Lematização vs Stemming**: simplemma é o default; RSLP e Snowball rodam em paralelo só para comparação. **Evidência:** lemma 16,97% > Snowball 10,30% > RSLP 7,58% de cobertura do glossário pós-processamento.
2. **D002 — Tokenização customizada** preservando tokens número+unidade (`4160V`, `60Hz`, `IP55`, `IE3`) como unidades atômicas.
3. **D003 — Expansão de abreviações** (40+ entradas) ANTES da tokenização — `rot.` e `rotação` viram o mesmo token.
4. **D004 — Normalização de unidades** (regex): `kw`/`KW`/`Kw` → `kW`; `IP 55` → `IP55`; `MOhm` → `MΩ`.
5. **D005 — Normalização de fabricantes** (28 regras): `Weg`/`WEG S.A.`/`W.E.G.` → `WEG`; `Leroy-Somer` → `Nidec`; etc. **Validação empírica:** 12/100 docs com variantes no raw → 0/100 no processado (100% normalizados).
6. **D006 — Stopwords técnicas customizadas** — base NLTK PT modificada (4 termos removidos por serem sensíveis ao domínio + 13 ruídos de planta adicionados).
7. **D007 — Detecção de idioma** por heurística PT/EN no documento (não por sentença — deliberadamente simples).
8. **D008 — Origem do corpus**: sintético com seed=42 (variações intencionais para exercitar o pipeline).
9. **D009 — Naming convention**: `DOC-{:05d}` / `GLOSS-{:03d}` / asset_tag `{prefix}-{nnn}-{letra}` / datas ISO 8601.

## Stack

`simplemma` (lematização PT, puro-python) · `nltk` (stemming RSLP + Snowball) · `pandas` · `matplotlib` · `seaborn`. Optou-se por `simplemma` em vez de `spaCy` para evitar download de ~500 MB de modelo — entrega mais rápida e com cobertura de PT-BR técnico equivalente para os tokens do glossário.
