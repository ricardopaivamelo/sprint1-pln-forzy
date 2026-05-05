# Perguntas Abertas — Sprint 1 PLN

Estas perguntas precisam ser respondidas (por você, pela banca, ou por decisão fundamentada nossa) **antes** de fechar o plano mestre. Cada uma muda o escopo e o cronograma.

---

## 🔴 Bloqueantes (sem isso, não há plano)

### Q1. Existe corpus de texto fornecido pela FIAP/Forzy?
O brief lista as fontes ("placas, manuais, fichas de cadastro, logs de operação") mas não diz se você **recebeu os arquivos** ou se precisa **coletar/sintetizar**.

- **Caminho A — corpus fornecido:** sabemos volume e formato → vamos direto para o pipeline.
- **Caminho B — você coleta:** precisaremos coletar PDFs de catálogos públicos (WEG, Siemens, ABB) + extrair texto via OCR/parser.
- **Caminho C — você gera sintético:** simular textos baseado nas normas IEC 60034 / ISO 10816. Mais rápido mas exige justificativa metodológica.

> **Resposta:** _____________________________________________________________

### Q2. Qual o **prazo final** de entrega da Sprint 1?
Sem deadline, não há cronograma realista.

> **Resposta:** _____________________________________________________________

### Q3. Trabalho **individual ou em grupo**? Se em grupo, quantos integrantes?
Define divisão de tarefas no plano e cobertura paralela.

> **Resposta:** _____________________________________________________________

### Q4. Volume mínimo de documentos esperado pela banca?
O brief não especifica. Sugiro **300–500 documentos** como mínimo defensável. Se você tem expectativa diferente, avisa.

> **Resposta:** _____________________________________________________________

---

## 🟡 Importantes (definem decisões técnicas)

### Q5. Stack tem restrições?
Algumas faculdades exigem ferramenta específica. Pode usar livremente **spaCy + NLTK + pandas**? Ou tem obrigação de usar Hugging Face / outro?

> **Resposta:** _____________________________________________________________

### Q6. Idiomas: proporção PT vs EN no corpus final?
- Opção A: 100% PT-BR (mais simples, glossário PT/EN como **referência**).
- Opção B: 70% PT / 30% EN (mais realista para placas/manuais industriais).
- Opção C: bilíngue paralelo (mesma descrição em ambos idiomas — exige mais trabalho).

> **Resposta:** _____________________________________________________________

### Q7. Granularidade do glossário: quantos termos no mínimo?
Sugiro **≥ 100 termos** distribuídos nas 6 categorias propostas no `ANALYSIS.md` §2.

> **Resposta:** _____________________________________________________________

### Q8. Critério de avaliação: você tem rubrica/grade da disciplina?
Se sim, anexar. Se não, vou trabalhar com os critérios sugeridos no `ANALYSIS.md` §5.

> **Resposta:** _____________________________________________________________

### Q9. Vai entregar via **Drive** ou **GitHub privado**?
Define naming convention dos artefatos e necessidade de README orientado a leitor da banca.

> **Resposta:** _____________________________________________________________

---

## 🟢 Decisões metodológicas (posso decidir e você valida)

### Q10. Tokenizer: spaCy customizado ou regex puro?
**Sugestão:** spaCy `pt_core_news_lg` com **regra customizada** para tokens de número+unidade (`4160V`, `60Hz`, `IP55`, `IE3`). Documentar a regra.

> **Aprova?** ☐ Sim  ☐ Não — explicar:

### Q11. Lematização vs Stemming: qual usar como default?
**Sugestão:** **Lematização** como default (preserva terminologia). Rodar **stemming** em paralelo apenas para a seção de comparação que o brief pede.

> **Aprova?** ☐ Sim  ☐ Não — explicar:

### Q12. Stopwords: lista 100% customizada ou base NLTK + remoções/adições?
**Sugestão:** Começar com `nltk.corpus.stopwords.words('portuguese')`, **remover** termos sensíveis ao domínio (`sem`, `com`, `sob`) e **adicionar** ruídos específicos de placas/logs (`ref`, `serie`, `nº`).

> **Aprova?** ☐ Sim  ☐ Não — explicar:

### Q13. Formato do glossário: JSON ou CSV?
**Sugestão:** **JSON Lines** (`.jsonl`) para flexibilidade de campos aninhados (abreviações, exemplos), com **export CSV achatado** como entrega secundária.

> **Aprova?** ☐ Sim  ☐ Não — explicar:

### Q14. Vamos versionar tudo em **Git** desde o dia 1?
**Sugestão:** Sim — repo local → GitHub privado quando tiver pelo menos a estrutura básica. Commits incrementais (não 1 commit gigante na entrega).

> **Aprova?** ☐ Sim  ☐ Não — explicar:

---

## Como responder

1. Edita este arquivo direto e preenche as respostas.
2. Ou cola aqui no chat as respostas em ordem (Q1, Q2, ...).
3. Quando tudo estiver respondido (ou marcado como "decidir agora"), gero o `plano_sprint1_nlp.md` com fases, cronograma e tarefas executáveis.
