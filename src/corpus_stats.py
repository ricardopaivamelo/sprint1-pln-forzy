"""Estatísticas do corpus + comparação lematização vs stemming.

Produz:
    - vocabulário total (V), tokens totais (N), hapax legomena
    - frequência por token (Counter)
    - comprimento médio dos documentos
    - cobertura do glossário (quantos termos do glossário aparecem no corpus)
    - métrica de comparação lema vs stem: redução de vocabulário e cobertura do glossário pós-processamento
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path


def carregar_glossario(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    termos = set()
    for entry in data.get("terms", []):
        for k in ("pt", "en"):
            v = entry.get(k, "")
            if v:
                for tok in v.lower().split():
                    termos.add(tok)
        for abrev in entry.get("abbreviations", []):
            termos.add(abrev.lower())
    return termos


def carregar_processed(path: Path) -> list[dict]:
    docs: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            docs.append(json.loads(line))
    return docs


def estat_basicas(docs: list[dict]) -> dict:
    tokens_all: list[str] = []
    lengths: list[int] = []
    for d in docs:
        toks = d.get("tokens_no_stopwords", [])
        tokens_all.extend(toks)
        lengths.append(len(toks))
    counter = Counter(tokens_all)
    vocab = set(counter.keys())
    hapax = [t for t, c in counter.items() if c == 1]
    return {
        "n_documentos": len(docs),
        "tokens_totais_N": len(tokens_all),
        "vocabulario_V": len(vocab),
        "type_token_ratio": len(vocab) / max(1, len(tokens_all)),
        "comprimento_medio_tokens": statistics.mean(lengths) if lengths else 0,
        "comprimento_mediano_tokens": statistics.median(lengths) if lengths else 0,
        "comprimento_min": min(lengths) if lengths else 0,
        "comprimento_max": max(lengths) if lengths else 0,
        "hapax_legomena_count": len(hapax),
        "hapax_taxa_perc": 100 * len(hapax) / max(1, len(vocab)),
        "top20_termos": counter.most_common(20),
    }


def cobertura_glossario(docs: list[dict], glossario_terms: set[str], campo: str) -> dict:
    """Mede quantos termos do glossário aparecem em determinado campo do corpus."""
    bag = set()
    for d in docs:
        for t in d.get(campo, []):
            bag.add(t.lower())
    achados = bag & glossario_terms
    return {
        "termos_glossario_unicos_no_corpus": len(achados),
        "tamanho_glossario": len(glossario_terms),
        "cobertura_perc": 100 * len(achados) / max(1, len(glossario_terms)),
    }


def comparar_lema_stem(docs: list[dict], glossario_terms: set[str]) -> dict:
    """Comparação 3-way: Lematização (simplemma) × RSLP × Snowball.

    Métrica central: cobertura do glossário pós-processamento. Quanto da
    terminologia técnica continua reconhecível depois da redução morfológica.
    Lematização é o default; stemmings entram como controles comparativos.
    """
    lemmas_all = [t for d in docs for t in d.get("lemmas", [])]
    rslp_all = [t for d in docs for t in d.get("stems_rslp", d.get("stems", []))]
    snow_all = [t for d in docs for t in d.get("stems_snowball", [])]

    cov_lema = cobertura_glossario(docs, glossario_terms, "lemmas")
    cov_rslp = cobertura_glossario(
        docs, glossario_terms,
        "stems_rslp" if any("stems_rslp" in d for d in docs) else "stems",
    )
    cov_snow = cobertura_glossario(docs, glossario_terms, "stems_snowball")

    return {
        "lemmas": {
            "tokens_totais": len(lemmas_all),
            "vocabulario_unico": len(set(lemmas_all)),
            "cobertura_glossario_perc": cov_lema["cobertura_perc"],
        },
        "stems_rslp": {
            "tokens_totais": len(rslp_all),
            "vocabulario_unico": len(set(rslp_all)),
            "cobertura_glossario_perc": cov_rslp["cobertura_perc"],
        },
        "stems_snowball": {
            "tokens_totais": len(snow_all),
            "vocabulario_unico": len(set(snow_all)),
            "cobertura_glossario_perc": cov_snow["cobertura_perc"],
        },
    }


def gerar_relatorio(processed_path: Path, glossario_path: Path, out_path: Path) -> dict:
    docs = carregar_processed(processed_path)
    gloss = carregar_glossario(glossario_path)
    rep = {
        "estatisticas_basicas": estat_basicas(docs),
        "cobertura_glossario_tokens": cobertura_glossario(docs, gloss, "tokens_no_stopwords"),
        "comparacao_lematizacao_vs_stemming": comparar_lema_stem(docs, gloss),
        "distribuicao_por_fonte": dict(Counter(d["source"] for d in docs)),
        "distribuicao_por_idioma": dict(Counter(d["language"] for d in docs)),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    return rep


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    rep = gerar_relatorio(
        processed_path=base / "data" / "processed" / "corpus_processed.jsonl",
        glossario_path=base / "data" / "reference" / "glossario_motores.json",
        out_path=base / "data" / "processed" / "corpus_stats.json",
    )
    print(json.dumps(rep, ensure_ascii=False, indent=2))
