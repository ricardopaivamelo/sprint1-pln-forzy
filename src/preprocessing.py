"""Pipeline de pré-processamento textual para corpus técnico de motores elétricos.

Etapas (Entregável 2 do brief):
    1. Expansão de abreviações industriais (rot.->rotação, tens.->tensão, etc.)
    2. Normalização de unidades físicas (kw/KW/Kw -> kW; IP 55 -> IP55)
    3. Normalização de fabricantes (Weg/W.E.G./WEG S.A. -> WEG)
    4. Tokenização preservando token de número+unidade (4160V, 60Hz, IP55, IE3)
    5. Remoção de stopwords técnicas customizadas
    6. Lematização (simplemma) + stemming (RSLP, Snowball) em paralelo
    7. Detecção de idioma por documento

Decisão metodológica: lematização é o default (preserva terminologia);
stemmings são gerados em paralelo apenas para a comparação que o brief exige.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Recursos lexicais
# ---------------------------------------------------------------------------

ABREVIACOES = {
    "rot.": "rotação",
    "tens.": "tensão",
    "corr.": "corrente",
    "pot.": "potência",
    "freq.": "frequência",
    "fabr.": "fabricante",
    "fab.": "fabricante",
    "isol.": "isolação",
    "iso.": "isolação",
    "rol.": "rolamento",
    "lub.": "lubrificação",
    "manut.": "manutenção",
    "vibr.": "vibração",
    "alt.": "altitude",
    "amb.": "ambiente",
    "sobreaq.": "sobreaquecimento",
    "sobrec.": "sobrecarga",
    "desbal.": "desbalanceamento",
    "desalin.": "desalinhamento",
    "harm.": "harmônicos",
    "term.": "terminal",
    "wdg.": "enrolamento",
    "brg.": "rolamento",
    "eff.": "rendimento",
    "máx.": "máximo",
    "mín.": "mínimo",
    "tn.": "torque nominal",
    "pn.": "potência nominal",
    "un.": "tensão nominal",
    "in.": "corrente nominal",
    "nº": "número",
    "nº série": "número de série",
    "s/n": "número de série",
    "ref.": "referência",
    "cl.": "classe",
    "trif.": "trifásico",
    "ind.": "industrial",
    "elét.": "elétrico",
    "últ.": "última",
    "próx.": "próxima",
    "op.": "operador",
    "téc.manut.": "técnico de manutenção",
    "os": "ordem de serviço",
    "pdm": "manutenção preditiva",
}

NORMALIZACAO_UNIDADES = [
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(kW|KW|Kw|kw)\b"), r"\1 kW"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(RPM|Rpm|rpm)\b"), r"\1 RPM"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(Hz|HZ|hz)\b"), r"\1 Hz"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(MΩ|MOhm|MOHM|mohm)\b"), r"\1 MΩ"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(Nm|N\.m|N·m)\b"), r"\1 Nm"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(°C|ºC|graus C|graus celsius)\b", re.IGNORECASE), r"\1 °C"),
    (re.compile(r"\bIP\s+(\d{2})\b"), r"IP\1"),
    (re.compile(r"\bIE\s+([1-5])\b"), r"IE\1"),
    (re.compile(r"\bclasse\s+([FHB])\b", re.IGNORECASE), r"classe \1"),
]

NORMALIZACAO_FABRICANTES = [
    # Ordem importa: padrões mais específicos primeiro para não serem
    # capturados pelo standalone (ex.: "Siemens AG" antes de "SIEMENS").
    (re.compile(r"\bWEG\s+Equipamentos[\s\w.]*\b", re.IGNORECASE), "WEG"),
    (re.compile(r"\bWEG\s+Motores[\s\w.]*\b", re.IGNORECASE), "WEG"),
    (re.compile(r"\bWEG\s+S\.?\s*A\.?\b", re.IGNORECASE), "WEG"),
    (re.compile(r"\bW\.E\.G\.?\b", re.IGNORECASE), "WEG"),
    (re.compile(r"\bWeg\b"), "WEG"),
    (re.compile(r"\bSiemens\s+AG\b", re.IGNORECASE), "Siemens"),
    (re.compile(r"\bSiemens\s+Industrial\b", re.IGNORECASE), "Siemens"),
    (re.compile(r"\bSIEMENS\b"), "Siemens"),
    (re.compile(r"\bA\.B\.B\.?\b"), "ABB"),
    (re.compile(r"\bABB\s+Motors\b", re.IGNORECASE), "ABB"),
    (re.compile(r"\bABB\s+Ltda\b", re.IGNORECASE), "ABB"),
    (re.compile(r"\bLeroy[\s\-]?Somer\b", re.IGNORECASE), "Nidec"),
    (re.compile(r"\bUS\s+Motors\b", re.IGNORECASE), "Nidec"),
    (re.compile(r"\bNidec\s+Motors\b", re.IGNORECASE), "Nidec"),
    (re.compile(r"\bNIDEC\b"), "Nidec"),
    (re.compile(r"\bSEW[\s\-]?Eurodrive\b", re.IGNORECASE), "SEW-Eurodrive"),
    # Standalone SEW só casa se NÃO for seguido de hífen ou "Eurodrive"
    # (evita duplicar 'SEW-Eurodrive' -> 'SEW-Eurodrive-Eurodrive')
    (re.compile(r"\bSEW(?![-\s]Eurodrive)\b"), "SEW-Eurodrive"),
    (re.compile(r"\bBaldor\s+Electric\b", re.IGNORECASE), "Baldor"),
    (re.compile(r"\bBaldor[\s\-]?Reliance\b", re.IGNORECASE), "Baldor"),
    (re.compile(r"\bBALDOR\b"), "Baldor"),
    (re.compile(r"\bVoges\s+Motores\b", re.IGNORECASE), "Voges"),
    (re.compile(r"\bVOGES\b"), "Voges"),
    (re.compile(r"\bToshiba\s+Industrial\b", re.IGNORECASE), "Toshiba"),
    (re.compile(r"\bTOSHIBA\b"), "Toshiba"),
    (re.compile(r"\bEberle\s+Motores\b", re.IGNORECASE), "Eberle"),
    (re.compile(r"\bEBERLE\b"), "Eberle"),
]

STOPWORDS_GENERICAS_PT = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das",
    "e", "é", "ou",
    "para", "por", "pelo", "pela", "pelos", "pelas",
    "no", "na", "nos", "nas", "em",
    "ao", "à", "aos", "às",
    "que", "se", "qual", "quais",
    "este", "esta", "estes", "estas", "isto",
    "esse", "essa", "esses", "essas", "isso",
    "ele", "ela", "eles", "elas",
    "com", "como", "já",
    "também", "ainda", "mais", "muito", "pouco",
    "ser", "ter", "estar", "haver",
    "foi", "era", "está", "estava",
    "será", "serão", "seria",
    "tem", "têm", "teve",
}

STOPWORDS_REMOVER = {"sem", "sob", "ate", "até"}
STOPWORDS_ADICIONAR_DOMINIO = {
    "sr", "sra", "etc", "obs", "ref", "modelo", "tipo",
    "favor", "verificar", "deve", "devem", "podem", "pode",
}

STOPWORDS_TECNICAS = (STOPWORDS_GENERICAS_PT - STOPWORDS_REMOVER) | STOPWORDS_ADICIONAR_DOMINIO

TOKEN_NUM_UNIDADE_RE = re.compile(
    r"\b\d+[.,]?\d*\s*(?:kW|KW|kw|cv|CV|V|kV|KV|Hz|HZ|hz|RPM|rpm|°C|mm/s|MΩ|Ω|A|mA|Nm|N\.m|"
    r"IP\d{2}|IE[1-4]|Y-Δ|Y/D)\b"
)
ALPHANUM_RE = re.compile(r"[a-zà-úA-ZÀ-Ú0-9_]+")


def remove_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# Tokenização e normalização
# ---------------------------------------------------------------------------

def expandir_abreviacoes(text: str) -> str:
    """Expande abreviações industriais. Aplica match case-insensitive ancorado."""
    out = text
    for abrev, expand in sorted(ABREVIACOES.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r"\b" + re.escape(abrev) + r"(?!\w)", re.IGNORECASE)
        out = pattern.sub(expand, out)
    return out


def normalizar_unidades(text: str) -> str:
    """Padroniza variações de unidades físicas (kw/KW/Kw -> kW; IP 55 -> IP55).

    Resolve ambiguidades de grafia em placas e fichas: '4kw' e '4 kW' devem
    aparecer como o mesmo token no vocabulário das próximas sprints.
    """
    out = text
    for pattern, replacement in NORMALIZACAO_UNIDADES:
        out = pattern.sub(replacement, out)
    return out


def normalizar_fabricantes(text: str) -> str:
    """Uniformiza variações de nomes de fabricantes para forma canônica.

    Resolve ambiguidades de nomenclatura entre placa, manual e ficha:
    'Weg', 'WEG S.A.', 'W.E.G.' -> 'WEG'. Atende ao requisito do brief de
    'resolver ambiguidades de nomenclatura'.
    """
    out = text
    for pattern, canonical in NORMALIZACAO_FABRICANTES:
        out = pattern.sub(canonical, out)
    return out


def normalizar(text: str) -> str:
    """Pipeline de normalização textual.

    Ordem: limpeza de espaços -> abreviações -> unidades -> fabricantes ->
    lowercase -> remoção de acentos -> colapso de whitespace.
    A normalização de unidades e fabricantes acontece ANTES do lowercase
    para que os regex possam casar com formas como 'WEG S.A.' ou 'IP 55'.
    """
    t = text.replace("\\n", " ").replace("\n", " ")
    t = expandir_abreviacoes(t)
    t = normalizar_unidades(t)
    t = normalizar_fabricantes(t)
    t = t.lower()
    t = remove_acentos(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def proteger_tokens_compostos(text: str) -> tuple[str, dict[str, str]]:
    """Substitui tokens número+unidade por placeholders preserváveis pelo tokenizer.

    Ex.: '4160V' -> '__TOKCOMP_0__', mapping {'__TOKCOMP_0__': '4160v'}
    """
    mapping: dict[str, str] = {}

    def _sub(m: re.Match) -> str:
        idx = len(mapping)
        key = f"__tokcomp_{idx}__"
        mapping[key] = m.group(0).lower().replace(" ", "")
        return key

    protected = TOKEN_NUM_UNIDADE_RE.sub(_sub, text)
    return protected, mapping


def tokenizar(text: str) -> list[str]:
    """Tokenização customizada com proteção de tokens compostos número+unidade."""
    protected, mapping = proteger_tokens_compostos(text)
    norm = normalizar(protected)
    tokens = ALPHANUM_RE.findall(norm)
    restored = [mapping.get(tok, tok) for tok in tokens]
    return restored


def remover_stopwords(tokens: Iterable[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS_TECNICAS and len(t) > 1]


# ---------------------------------------------------------------------------
# Lematização e stemming
# ---------------------------------------------------------------------------

def _carregar_simplemma():
    """simplemma é puro-python e não precisa baixar modelo (vs spaCy ~500MB)."""
    try:
        import simplemma  # noqa: WPS433
        return simplemma
    except ImportError:
        return None


def _carregar_rslp():
    try:
        import nltk  # noqa: WPS433
        from nltk.stem import RSLPStemmer  # noqa: WPS433
        try:
            return RSLPStemmer()
        except LookupError:
            nltk.download("rslp", quiet=True)
            return RSLPStemmer()
    except ImportError:
        return None


def _carregar_snowball():
    try:
        from nltk.stem import SnowballStemmer  # noqa: WPS433
        return SnowballStemmer("portuguese")
    except (ImportError, LookupError):
        return None


_LEMMER = None
_STEMMER_RSLP = None
_STEMMER_SNOW = None


def lematizar(tokens: list[str]) -> list[str]:
    """Lematização via simplemma (PT). Fallback: identidade (mantém token original).

    simplemma cobre PT moderno; tokens ausentes do dicionário voltam como estão.
    Para texto técnico industrial é cobertura suficiente — vocabulário base do
    domínio (motor, rolamento, tensão, etc.) está coberto.
    """
    global _LEMMER
    if _LEMMER is None:
        _LEMMER = _carregar_simplemma()
    if _LEMMER is None:
        return list(tokens)
    return [_LEMMER.lemmatize(t, lang="pt") for t in tokens]


def stemmizar_rslp(tokens: list[str]) -> list[str]:
    """Stemming via NLTK RSLPStemmer (algoritmo específico para PT-BR).

    RSLP é mais agressivo: remove sufixos com base em regras específicas do PT-BR.
    Tende a destruir terminologia técnica ('rolamento' -> 'rolament').
    """
    global _STEMMER_RSLP
    if _STEMMER_RSLP is None:
        _STEMMER_RSLP = _carregar_rslp()
    if _STEMMER_RSLP is None:
        return list(tokens)
    return [_STEMMER_RSLP.stem(t) for t in tokens]


def stemmizar_snowball(tokens: list[str]) -> list[str]:
    """Stemming via NLTK SnowballStemmer (Porter2 adaptado para PT).

    Snowball é menos agressivo que RSLP e cobre vários idiomas com mesmo algoritmo.
    Usado como ponto intermediário na comparação RSLP × Snowball × Lematização.
    """
    global _STEMMER_SNOW
    if _STEMMER_SNOW is None:
        _STEMMER_SNOW = _carregar_snowball()
    if _STEMMER_SNOW is None:
        return list(tokens)
    return [_STEMMER_SNOW.stem(t) for t in tokens]


# Alias retrocompatível: API antiga `stemmizar` continua existindo apontando pra RSLP.
def stemmizar(tokens: list[str]) -> list[str]:
    return stemmizar_rslp(tokens)


# ---------------------------------------------------------------------------
# Detecção de idioma (heurística leve, fallback langid)
# ---------------------------------------------------------------------------

WORDS_EN = {"motor", "rated", "voltage", "current", "frame", "class", "bearing", "the", "of", "for", "with"}
WORDS_PT = {"motor", "tensão", "corrente", "rotação", "potência", "rolamento", "classe", "para", "com", "de"}


def detectar_idioma(text: str) -> str:
    """Heurística simples por contagem de stopwords PT/EN. Suficiente para o domínio."""
    norm = remove_acentos(text.lower())
    pt = sum(1 for w in WORDS_PT if remove_acentos(w) in norm)
    en = sum(1 for w in WORDS_EN if w in norm)
    if pt > 0 and en > 0 and abs(pt - en) <= 1:
        return "mixed"
    if pt >= en:
        return "pt"
    return "en"


# ---------------------------------------------------------------------------
# Pipeline integrado
# ---------------------------------------------------------------------------

@dataclass
class ProcessedDoc:
    doc_id: str
    raw_text: str
    normalized_text: str
    tokens: list[str]
    tokens_no_stopwords: list[str]
    lemmas: list[str]
    stems_rslp: list[str]
    stems_snowball: list[str]
    detected_language: str
    source: str
    asset_tag: str
    field: str
    extraction_date: str

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "asset_tag": self.asset_tag,
            "source": self.source,
            "field": self.field,
            "language": self.detected_language,
            "extraction_date": self.extraction_date,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "tokens": self.tokens,
            "tokens_no_stopwords": self.tokens_no_stopwords,
            "lemmas": self.lemmas,
            "stems_rslp": self.stems_rslp,
            "stems_snowball": self.stems_snowball,
            # Alias retrocompatível para o stats antigo:
            "stems": self.stems_rslp,
            "preprocessing_version": "1.1",
        }


def processar_doc(raw_doc: dict) -> ProcessedDoc:
    raw = raw_doc["raw_text"]
    norm = normalizar(raw)
    tokens = tokenizar(raw)
    tokens_clean = remover_stopwords(tokens)
    lemmas = lematizar(tokens_clean)
    stems_rslp = stemmizar_rslp(tokens_clean)
    stems_snow = stemmizar_snowball(tokens_clean)
    lang = detectar_idioma(raw)
    return ProcessedDoc(
        doc_id=raw_doc["doc_id"],
        raw_text=raw,
        normalized_text=norm,
        tokens=tokens,
        tokens_no_stopwords=tokens_clean,
        lemmas=lemmas,
        stems_rslp=stems_rslp,
        stems_snowball=stems_snow,
        detected_language=lang,
        source=raw_doc["source"],
        asset_tag=raw_doc.get("asset_tag", ""),
        field=raw_doc.get("field", ""),
        extraction_date=raw_doc.get("extraction_date", ""),
    )


def processar_corpus(in_path: Path, out_path: Path) -> list[ProcessedDoc]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    processed: list[ProcessedDoc] = []
    with in_path.open("r", encoding="utf-8") as fh, out_path.open("w", encoding="utf-8") as out:
        for line in fh:
            raw = json.loads(line)
            p = processar_doc(raw)
            processed.append(p)
            out.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")
    return processed


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    in_path = base / "data" / "raw" / "corpus_raw.jsonl"
    out_path = base / "data" / "processed" / "corpus_processed.jsonl"
    docs = processar_corpus(in_path, out_path)
    print(f"[ok] {len(docs)} documentos processados em {out_path}")
    print(f"[exemplo doc 0] raw: {docs[0].raw_text[:120]}...")
    print(f"[exemplo doc 0] normalized: {docs[0].normalized_text[:120]}...")
    print(f"[exemplo doc 0] tokens(sem sw): {docs[0].tokens_no_stopwords[:15]}")
    print(f"[exemplo doc 0] lemmas: {docs[0].lemmas[:15]}")
    print(f"[exemplo doc 0] stems RSLP: {docs[0].stems_rslp[:15]}")
    print(f"[exemplo doc 0] stems Snowball: {docs[0].stems_snowball[:15]}")
