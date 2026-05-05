# Análise Técnica do Brief — Sprint 1 PLN (Forzy)

**Documento-fonte:** [`../briefing/sprintNLP.txt`](../briefing/sprintNLP.txt)
**Data da análise:** 2026-05-05

---

## 1. Leitura do Brief em uma Frase

> "Construa o **corpus textual base** do digital twin: padronize termos, limpe textos heterogêneos e entregue um dataset estruturado com glossário e pipeline reproduzível."

A sprint é de **engenharia de corpus**, não de modelagem. O eixo avaliativo provável recai sobre **rigor metodológico** das decisões de normalização, **qualidade do glossário** e **reprodutibilidade** do notebook.

---

## 2. Decomposição dos Entregáveis

### Entregável 1 — Inventário e Padronização Terminológica

**O que pedem:**
- Levantar termos técnicos recorrentes em motores elétricos: tensão, corrente, RPM, potência, TAGs, fabricantes, tipos de falha.
- Glossário **bilíngue PT/EN** que resolva ambiguidades entre **documentação técnica** (formal), **placa do equipamento** (abreviado, símbolos) e **registros operacionais** (informais, com gírias de planta).
- Definir **campos textuais obrigatórios** do cadastro do ativo: descrição, TAG, localização, especificação técnica — com **vocabulário controlado**.

**Decisões implícitas que precisam ser explicitadas:**
- Granularidade do glossário: termo isolado vs. expressão composta (ex.: "rolamento de esferas" como entrada única ou "rolamento" + "esferas"?).
- Direção da tradução: PT→EN, EN→PT ou bidirecional simétrica?
- Política para acrônimos: criar entrada separada ("RPM", "kW") ou agrupar com forma extensa?
- Como tratar **fabricantes**: nomes próprios entram no glossário como entidades? (Ex.: WEG, Siemens, ABB.)

**Estrutura de dados sugerida (proposta para validar):**
```json
{
  "term_id": "GLOSS-0001",
  "pt": "rolamento de esferas",
  "en": "ball bearing",
  "category": "componente_mecanico | grandeza_eletrica | falha | norma | unidade",
  "abbreviations": ["rol.", "ball brg."],
  "definition_pt": "...",
  "definition_en": "...",
  "controlled_vocab_field": "descricao | especificacao | tag | localizacao",
  "source_norm": "IEC 60034-1",
  "examples": ["rolamento de esferas 6309 ZZ"]
}
```

### Entregável 2 — Pipeline de Pré-processamento Textual

**Etapas obrigatórias do brief:**
1. **Tokenização** — separar tokens. Para texto técnico, tokenizadores genéricos quebram unidades ("4160V" vira "4160" + "V"; "6.000 RPM" perde o ponto decimal). Decisão: usar regex customizado que preserva **número+unidade** como token único.
2. **Remoção de stopwords técnicas** — observação crítica: stopwords genéricas em PT (`nltk.corpus.stopwords.words('portuguese')`) **podem remover termos relevantes** ao domínio. Ex.: "sem" em "motor sem carga" carrega informação operacional. Lista customizada é mandatória.
3. **Tratamento de abreviações industriais** — exemplo do brief: `rot.` → `rotação`, `tens.` → `tensão`. Precisa-se de **dicionário de expansão** baseado em corpus real. Deve ser construído iterativamente.
4. **Multilíngue** — mistura PT/EN/abreviações de norma na mesma frase é comum em placas (ex.: "MOTOR TRIFÁSICO IND. 60Hz - IP55 - F class - IE3"). Estratégia: detecção de idioma por **trecho** (não por documento), via langid/fastText, ou heurística por dicionário.
5. **Lematização vs Stemming** — o brief pede **avaliar impacto na qualidade do corpus**. Recomendação metodológica:
   - **Lematização (spaCy `pt_core_news_lg`)**: preserva formas técnicas íntegras; recomendado para vocabulário controlado.
   - **Stemming (Snowball/RSLP)**: agressivo em PT-BR; destrói terminologia ("rolamento" → "rolament", "lubrificação" → "lubrific"). Útil só para análise de frequência.
   - **Decisão:** rodar **ambos** e medir cobertura do glossário pós-processamento. O brief explicitamente pede a comparação.
6. **Estatísticas do corpus**: vocabulário total (V), frequência de termos (Zipf), comprimento médio de descrições, taxa de hapax legomena (termos com freq=1 → indicador de ruído ou vocabulário esparso).

### Entregável 3 — Corpus Textual Estruturado e Documentado

**O que pedem:**
- JSON/CSV consolidado com **metadados por registro**: campo (descrição/TAG/localização/etc.), fonte (placa/manual/ficha/log), data de extração, idioma.
- **Documentar decisões** de padronização e regras de normalização aplicadas.
- **Estrutura de diretórios** e **naming convention** para sprints futuras.

**Schema sugerido (proposta):**
```json
{
  "doc_id": "DOC-2026-00001",
  "asset_tag": "M-101-A",
  "field": "descricao | tag | localizacao | especificacao_tecnica | log_operacao",
  "source": "placa | manual | ficha_cadastro | log_operacional",
  "language": "pt | en | mixed",
  "extraction_date": "2026-05-05",
  "raw_text": "MOTOR TRIFÁSICO IND. 60Hz - IP55 - F class - IE3",
  "normalized_text": "motor trifasico industrial 60 hz ip55 classe f ie3",
  "tokens": ["motor", "trifasico", "industrial", "60_hz", "ip55", "classe_f", "ie3"],
  "lemmas": ["motor", "trifasico", "industrial", "60_hz", "ip55", "classe_f", "ie3"],
  "detected_terms": ["GLOSS-0042", "GLOSS-0103"],
  "preprocessing_version": "1.0"
}
```

---

## 3. Stack Tecnológico Sugerido (a validar)

| Componente | Opção principal | Alternativa | Justificativa |
|------------|-----------------|-------------|----------------|
| Tokenização | `spaCy pt_core_news_lg` | `nltk.tokenize` | spaCy mantém pipeline integrado (tokens + lemmas + POS) |
| Stopwords | Lista customizada + base NLTK PT | — | Lista 100% pronta destrói domínio |
| Lematização | `spaCy` (PT-BR) | `simplemma` | spaCy tem modelo treinado em PT-BR; simplemma é mais leve |
| Stemming | `nltk.stem.RSLPStemmer` | Snowball PT | RSLP é específico para PT-BR |
| Detecção de idioma | `langid` ou `fasttext lid.176` | regex de ASCII | Multilíngue por sentença |
| Estatísticas | `collections.Counter`, `pandas` | — | KISS |
| Armazenamento | JSON Lines (`.jsonl`) + CSV de metadados | Apenas CSV | JSONL é amigável a campos aninhados |

`requirements.txt` mínimo previsto:
```
spacy>=3.7
nltk>=3.9
pandas>=2.2
langid>=1.1
simplemma>=0.9         # alternativa de lematização
matplotlib>=3.9
seaborn>=0.13
jsonschema>=4.23       # validar schema do corpus
python-dotenv>=1.0
```

E o modelo do spaCy PT precisa ser baixado:
```bash
python -m spacy download pt_core_news_lg
```

---

## 4. Riscos & Mitigações Iniciais

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Não temos corpus real (textos brutos) | **Alta** | **Alto** — sem entrada, sem entregáveis | Esclarecer com banca; alternativa: gerar corpus simulado a partir de catálogos públicos (WEG, Siemens) |
| Volume insuficiente (poucos textos → Zipf não converge) | Média | Médio | Mínimo de **300–500 documentos** para estatísticas terem sentido |
| Stopwords genéricas matarem termos do domínio | **Alta** | Alto | Lista customizada construída a partir do corpus real, com inspeção manual |
| Stemming destruir terminologia técnica | Alta | Médio | Avaliar e documentar; usar lematização como default |
| Glossário com baixa cobertura | Média | Alto | Construção iterativa: extrair candidatos do corpus, depois enriquecer com normas IEC |
| Mistura PT/EN não detectada | Média | Médio | Validação manual amostral (10% do corpus) |
| Reprodutibilidade do notebook | Baixa | Alto | Seeds fixadas, requirements pinados, modelo spaCy pinado |

---

## 5. Critérios de Sucesso (proposta)

Como o brief não dá pesos explícitos, sugiro estes mínimos:

**Glossário PT/EN**
- ≥ 100 termos cobrindo: grandezas elétricas, componentes mecânicos, modos de falha, normas, fabricantes, unidades.
- 100% dos termos com tradução PT↔EN.
- ≥ 20 abreviações industriais mapeadas com forma extensa.

**Pipeline**
- Notebook end-to-end em < 15 min em runtime limpo do Colab.
- Comparação documentada lematização vs stemming, com métrica clara (cobertura do glossário pós-processamento).
- Lista de stopwords técnicas justificada termo a termo.

**Corpus**
- ≥ 300 documentos normalizados.
- 100% com metadados completos (campo, fonte, idioma, data).
- Schema validado (JSON Schema).

---

## 6. Próximo Passo

Antes de gerar o **plano mestre** (`plano_sprint1_nlp.md` com fases, cronograma e cronograma diário), responder as perguntas abertas em [`QUESTIONS.md`](QUESTIONS.md). Sem isso, o plano vira chute.
