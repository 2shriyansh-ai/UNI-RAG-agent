# UNI-RAG Evaluation

This folder contains Shriyansh Tummala's evaluation and reliability contribution to the four-person UNI-RAG academic project.

## Benchmark categories

| Category | Purpose | Expected behaviour |
|---|---|---|
| `answerable` | Evidence exists in one document | Retrieve the source, answer, and cite it |
| `cross_document` | Evidence is distributed across documents | Retrieve and synthesize multiple sources |
| `ocr` | Evidence is inside an image or scanned page | Extract through OCR and cite the source |
| `unsupported` | Evidence is absent | Refuse instead of inventing an answer |
| `access_restricted` | Evidence exists but the role lacks permission | Deny access without leaking content |

## Five reported metrics

1. **Retrieval hit rate** — percentage of eligible cases retrieving at least one expected source.
2. **Citation coverage** — percentage of successful responses containing a citation.
3. **Refusal accuracy** — percentage of supported and unsupported cases handled correctly.
4. **Access-control accuracy** — percentage of restricted cases correctly refused.
5. **Average latency** — mean API response time in milliseconds.

These are automated behavioural checks, not a substitute for expert scoring of answer quality.

## Dataset format

Each line in the JSONL benchmark is one independent case:

```json
{"id":"single-001","category":"answerable","question":"...","expected_sources":["handbook.pdf"],"expect_refusal":false,"user_role":"student"}
```

Replace the sample questions and filenames with evidence from the locally indexed test corpus before reporting results.

## Expected API contract

Default request:

```json
{"question":"...","user_role":"student","retrieval_mode":"mmr"}
```

Default response:

```json
{"answer":"...","citations":[{"source":"handbook.pdf","page":3}],"sources":[{"source":"handbook.pdf"}],"refused":false}
```

Use `--answer-field`, `--citations-field`, `--sources-field`, and `--refused-field` when an API uses different response keys.

## Run

```bash
python evaluate.py --dataset benchmark.sample.jsonl --endpoint http://localhost:8000/query --output results/mmr --retrieval-mode mmr
python evaluate.py --dataset benchmark.sample.jsonl --endpoint http://localhost:8000/query --output results/similarity --retrieval-mode similarity
```

Compare the generated `results.json` summaries and inspect `results.csv` for failure cases.

## Honest reporting

Do not publish scores until:

- the questions are mapped to a fixed, versioned document corpus;
- expected sources and permissions have been manually checked;
- both retrieval modes run against the same corpus and configuration;
- failed requests are separated from incorrect RAG responses.
