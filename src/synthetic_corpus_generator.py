"""Gera corpus sintético de 100 documentos textuais sobre motores elétricos industriais.

4 categorias (heterogeneidade do brief): placa, manual, ficha_cadastro, log_operacional.
Reproduzível via seed=42.
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_DOCS = 100

FABRICANTES = ["WEG", "Siemens", "ABB", "Toshiba", "Voges", "Eberle", "Nidec", "Baldor"]
# Variações intencionais para exercitar a normalização de fabricantes do pipeline
FABRICANTES_VARIACOES = {
    "WEG": ["WEG", "Weg", "WEG S.A.", "W.E.G.", "WEG Motores S.A."],
    "Siemens": ["Siemens", "SIEMENS", "Siemens AG", "Siemens Industrial"],
    "ABB": ["ABB", "A.B.B.", "ABB Motors", "ABB Ltda"],
    "Nidec": ["Nidec", "NIDEC", "Nidec Motors", "Leroy-Somer"],
    "Baldor": ["Baldor", "BALDOR", "Baldor Electric", "Baldor-Reliance"],
    "Toshiba": ["Toshiba", "TOSHIBA", "Toshiba Industrial"],
    "Voges": ["Voges", "VOGES", "Voges Motores"],
    "Eberle": ["Eberle", "EBERLE", "Eberle Motores"],
}
TENSOES = [220, 380, 440, 460, 480, 575, 690, 2300, 4160, 6900, 13800]
POTENCIAS_KW = [7.5, 11, 15, 22, 37, 55, 75, 110, 150, 220, 315, 450, 600, 800, 1100, 1500, 2200, 3000, 4500, 7500]
RPMS = [1180, 1185, 1480, 1485, 1780, 1785, 3550, 3580]
POLOS = [2, 4, 6, 8]
FREQUENCIAS = [50, 60]
IPS = ["IP55", "IP56", "IP65", "IP66"]
CLASSES_ISO = ["F", "H"]
CLASSES_EFF = ["IE2", "IE3", "IE4"]
FRAMES = ["IEC 132M", "IEC 160L", "IEC 200L", "IEC 225M", "IEC 280S", "IEC 315M", "IEC 355M", "IEC 400L", "IEC 450L"]
TAGS_PREFIX = ["M", "MOT", "EM", "MIT"]
LOCALIZACOES = [
    "Sala de Compressores", "Casa de Bombas 02", "Linha de Produção A",
    "Galpão de Utilidades", "Subestação Norte", "Casa de Máquinas 1",
    "Área de Resfriamento", "Setor de Embalagens", "Linha 03 - Trefila",
    "Pátio de Manobras", "Torre de Resfriamento 04", "Estação Elevatória"
]
MODOS_FALHA = [
    "desgaste de rolamento", "desbalanceamento", "desalinhamento",
    "falha de isolação", "sobreaquecimento", "barra de rotor partida",
    "vazamento de graxa", "ruído anormal", "vibração elevada",
    "harmônicos elevados na rede"
]


def _tag(rng: random.Random) -> str:
    return f"{rng.choice(TAGS_PREFIX)}-{rng.randint(100, 999)}-{rng.choice('ABCD')}"


def _fab_var(rng: random.Random, canonico: str) -> str:
    """Retorna uma variação aleatória do nome do fabricante (canônico, abreviado, etc.).

    Garante que o pipeline tenha trabalho real de normalização — se sempre
    usássemos o nome canônico, não conseguiríamos provar que o
    NORMALIZACAO_FABRICANTES funciona.
    """
    return rng.choice(FABRICANTES_VARIACOES.get(canonico, [canonico]))


def _hoje_menos(rng: random.Random, dias_max: int = 720) -> str:
    """Gera data relativa a 2026-05-05.

    `dias_max` positivo → data no passado (até `dias_max` dias atrás).
    `dias_max` negativo → data no futuro (até `abs(dias_max)` dias à frente).
    """
    base = date(2026, 5, 5)
    if dias_max >= 0:
        delta = rng.randint(0, dias_max)
        return (base - timedelta(days=delta)).isoformat()
    delta = rng.randint(0, abs(dias_max))
    return (base + timedelta(days=delta)).isoformat()


def gen_placa(rng: random.Random) -> dict:
    """Texto de placa de identificação — abreviações fortes, mistura PT/EN."""
    fab_canonico = rng.choice(FABRICANTES)
    fab = _fab_var(rng, fab_canonico)
    pot = rng.choice(POTENCIAS_KW)
    tens = rng.choice(TENSOES)
    freq = rng.choice(FREQUENCIAS)
    rpm = rng.choice(RPMS)
    ip = rng.choice(IPS)
    classe = rng.choice(CLASSES_ISO)
    eff = rng.choice(CLASSES_EFF)
    frame = rng.choice(FRAMES)
    polos = rng.choice(POLOS)
    serial = f"{rng.randint(2018, 2026)}{rng.randint(10000, 99999)}"

    templates = [
        f"{fab} | MOTOR TRIF. IND. | Pn {pot} kW | Un {tens}V | {freq}Hz | rot. {rpm} RPM | {ip} | F class | {eff} | frame {frame} | S/N {serial}",
        f"FAB. {fab} - PN={pot}kW - UN={tens}V/{freq}Hz - {rpm}rpm - {polos} polos - cl. iso. {classe} - {ip} - {eff} - SN {serial}",
        f"{fab} TRIFASICO {pot}KW {tens}V {freq}HZ {rpm}RPM {ip} CLASSE {classe} {eff} FRAME {frame} NS {serial}",
        f"Motor de Indução Trifásico\\n{fab} - cv {round(pot * 1.341, 1)} - {pot} kW\\n{tens}V {freq}Hz {rpm} RPM\\n{ip} cl. {classe} - {eff}\\nNº Série: {serial}",
    ]
    raw = rng.choice(templates)
    return {
        "raw_text": raw,
        "source": "placa",
        "language": "mixed",
        "asset_tag": _tag(rng),
        "field": "especificacao_tecnica",
    }


def gen_manual(rng: random.Random) -> dict:
    """Trecho de manual técnico — texto formal, terminologia completa."""
    fab = rng.choice(FABRICANTES)
    pot = rng.choice(POTENCIAS_KW)
    tens = rng.choice(TENSOES)
    rpm = rng.choice(RPMS)

    templates = [
        f"O motor de indução trifásico {fab} de {pot} kW foi projetado para operar em tensão nominal de {tens} V e rotação nominal de {rpm} RPM, em conformidade com a norma IEC 60034-1. A isolação é classe F, com elevação máxima de temperatura de 80 K sobre temperatura ambiente de 40 °C.",
        f"Para garantir a vida útil dos rolamentos, recomenda-se lubrificação a cada 4000 horas de operação contínua. O fabricante {fab} especifica graxa polialfaolefina compatível com classe NLGI 2. A temperatura do mancal não deve ultrapassar 95 °C em regime de serviço S1.",
        f"Em caso de partida pesada, utilizar ligação estrela-triângulo (Y-Δ) ou soft-starter. A corrente de partida pode atingir até 7 vezes a corrente nominal, conforme categoria N da norma IEC 60034-12. Verificar dimensionamento do disjuntor e cabos de alimentação.",
        f"O grau de proteção {rng.choice(IPS)} garante operação em ambientes com presença de poeira e jatos de água. Não é recomendado o uso em atmosferas explosivas sem certificação ATEX adequada (norma IEC 60079).",
        f"A análise de vibração deve ser realizada conforme ISO 10816, com sensores instalados nos mancais dianteiro e traseiro. Valores RMS de velocidade acima de 4,5 mm/s indicam necessidade de inspeção. Acima de 7,1 mm/s, parada imediata é recomendada.",
        f"O motor {fab} {pot} kW classe IE3 atende aos requisitos de eficiência energética da norma IEC 60034-30-1. O rendimento mínimo a plena carga é de 94,5% para esta faixa de potência.",
        f"Antes da energização, verificar a resistência de isolamento dos enrolamentos com megôhmetro a 500 V. Valores abaixo de 100 MΩ indicam degradação do isolante e necessidade de secagem ou rebobinagem.",
        f"O alinhamento entre o motor e a carga deve ser verificado com relógio comparador ou sistema laser. Tolerância máxima paralela de 0,05 mm e angular de 0,1 mm/m. Desalinhamento excessivo causa desgaste prematuro de rolamentos.",
    ]
    raw = rng.choice(templates)
    return {
        "raw_text": raw,
        "source": "manual",
        "language": "pt",
        "asset_tag": _tag(rng),
        "field": "descricao",
    }


def gen_ficha(rng: random.Random) -> dict:
    """Ficha de cadastro do ativo — semi-estruturado com abreviações."""
    fab_canonico = rng.choice(FABRICANTES)
    fab = _fab_var(rng, fab_canonico)
    pot = rng.choice(POTENCIAS_KW)
    tens = rng.choice(TENSOES)
    rpm = rng.choice(RPMS)
    tag = _tag(rng)
    loc = rng.choice(LOCALIZACOES)

    templates = [
        f"TAG: {tag} | Descrição: Motor elétrico trifásico {fab} | Localização: {loc} | Pot.: {pot} kW | Tens. nom.: {tens} V | Rot.: {rpm} rpm | Cl. iso.: F | Fabr.: {fab} | Ano fabr.: {rng.randint(2015, 2025)}",
        f"Cadastro do Ativo\\nTAG: {tag}\\nDescrição: Motor de indução tipo gaiola, fabricação {fab}\\nLocal: {loc}\\nDados Nominais: {pot}kW / {tens}V / {rpm}RPM\\nTipo de serviço: S1\\nObservações: Equipamento crítico, plano de manutenção mensal.",
        f"Ativo {tag}: Motor elét. trif. ind. - {fab} - {pot}kW - {tens}V - {rpm}rpm - inst. em {loc} - últ. manut.: {_hoje_menos(rng, 180)}",
        f"FICHA TÉCNICA — TAG {tag}\\nFabricante: {fab}\\nModelo: W22-{rng.randint(100, 999)}-{rng.choice(['IR3', 'IR4'])}\\nPotência: {pot} kW ({round(pot * 1.341, 1)} cv)\\nTensão: {tens} V\\nFrequência: 60 Hz\\nRPM: {rpm}\\nClasse de isolação: F\\nGrau de proteção: {rng.choice(IPS)}\\nLocalização: {loc}",
    ]
    raw = rng.choice(templates)
    return {
        "raw_text": raw,
        "source": "ficha_cadastro",
        "language": "pt",
        "asset_tag": tag,
        "field": "descricao",
    }


def gen_log(rng: random.Random) -> dict:
    """Log operacional — informal, abreviações de planta, entradas curtas."""
    falha = rng.choice(MODOS_FALHA)
    tag = _tag(rng)
    operador = rng.choice(["JS", "MR", "CB", "AL", "RP", "Téc.Manut."])
    data_evento = _hoje_menos(rng, 365)

    templates = [
        f"[{data_evento} 14:32] {tag} - operador {operador} reportou ruído anormal no mancal LA. Vibr. medida: {round(rng.uniform(3.5, 9.0), 1)} mm/s. Suspeita de {falha}. Programar inspeção.",
        f"OS aberta {data_evento} - ativo {tag} - {falha} confirmado. Substituir rol. dianteiro 6309 ZZ. Tempo estimado parada: {rng.randint(2, 8)}h.",
        f"{data_evento} - rotina inspeção {tag}: temp. mancal {rng.randint(60, 105)}°C / vibr. {round(rng.uniform(1.5, 4.5), 1)} mm/s / corr. {round(rng.uniform(0.85, 1.05), 2)} x In. Status: OK.",
        f"ALERTA - {tag} - {data_evento} 03:15 - sobreaq. detectado pelo sistema PdM. Temp. enrol. atingiu {rng.randint(140, 165)}°C. Operação reduzida para 70% da nominal. Aguarda equipe manut.",
        f"REGISTRO {data_evento}: {tag} - desligamento por proteção térmica. Causa provável: {falha}. Op. {operador} - acionar manut. urgente.",
        f"Inspeção termográfica {data_evento}: ativo {tag} apresenta ponto quente na caixa de ligação ({rng.randint(80, 120)}°C). Ação: reaperto dos terminais e nova medição em 7 dias.",
        f"{data_evento} {operador}: troca preventiva de graxa concluída no {tag}. Próx. lubr. programada para {_hoje_menos(rng, -180)[:10]}. Sem anormalidades.",
        f"FALHA {tag} {data_evento} - desbal. detectado em análise espectral (1xRPM dominante). Pico em {rng.randint(28, 32)} Hz. Programar balanceamento dinâmico.",
    ]
    raw = rng.choice(templates)
    return {
        "raw_text": raw,
        "source": "log_operacional",
        "language": "pt",
        "asset_tag": tag,
        "field": "log_operacao",
    }


GENERATORS = {
    "placa": (gen_placa, 30),
    "manual": (gen_manual, 25),
    "ficha_cadastro": (gen_ficha, 25),
    "log_operacional": (gen_log, 20),
}


def generate_corpus(seed: int = SEED) -> list[dict]:
    """Gera os N_DOCS documentos com IDs e metadados completos."""
    rng = random.Random(seed)
    docs: list[dict] = []
    counter = 1
    for _, (fn, n) in GENERATORS.items():
        for _ in range(n):
            d = fn(rng)
            d["doc_id"] = f"DOC-{counter:05d}"
            d["extraction_date"] = "2026-05-05"
            d["preprocessing_version"] = "0.0-raw"
            docs.append(d)
            counter += 1
    rng.shuffle(docs)
    return docs


def save_corpus(docs: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for d in docs:
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "raw" / "corpus_raw.jsonl"
    docs = generate_corpus()
    save_corpus(docs, out)
    print(f"[ok] {len(docs)} documentos gerados em {out}")
    distro: dict[str, int] = {}
    for d in docs:
        distro[d["source"]] = distro.get(d["source"], 0) + 1
    print(f"[distribuição] {distro}")
