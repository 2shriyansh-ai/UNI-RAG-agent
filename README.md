# UNI-RAG Agent

An offline-first multimodal Retrieval-Augmented Generation system for grounded question answering across academic documents.

> Academic group project developed by a team of four. This repository preserves the original experimental modules and adds a separate evaluation and reliability layer maintained by [Shriyansh Tummala](https://github.com/2shriyansh-ai).

## What it does

UNI-RAG Agent processes heterogeneous documents, retrieves relevant evidence, and generates answers with source grounding. The project combines:

- PDF, DOCX, PPTX, and image ingestion
- OCR for image-based and scanned content
- MiniLM sentence embeddings
- ChromaDB vector storage
- Similarity and Maximal Marginal Relevance (MMR) retrieval
- Local Phi-3 inference through Ollama
- Citation-aware answers and access-control checks

## Architecture

```text
Documents -> Parsing/OCR -> Segmentation -> MiniLM Embeddings
          -> ChromaDB -> Similarity/MMR Retrieval -> Phi-3 via Ollama
          -> Grounded Answer + Citations
```

## Repository structure

- `Analyst/` — analysis-related components
- `Segmentation/` — document segmentation workflows
- `neural - Copy/` — neural-processing experiments
- `sih_multimodal_rag/` — multimodal RAG submodule
- `sih_multimodal_rag - Copy (2)/` — integrated experimental copy
- `evaluation/` — benchmark schema, automated evaluator, and reliability documentation

The original folder names are retained to preserve the team's project history.

## Evaluation and reliability layer

The evaluation module provides a reproducible way to test the RAG pipeline across five categories:

1. Answerable single-document questions
2. Cross-document questions
3. OCR-dependent questions
4. Unsupported questions that should be refused
5. Access-restricted questions

The evaluator records five core signals:

- Retrieval hit rate
- Citation coverage
- Refusal accuracy
- Access-control accuracy
- Response latency

It accepts a JSONL benchmark and calls a configurable HTTP endpoint, so it can be connected to the active UNI-RAG API without coupling the benchmark to one experimental module. See [evaluation/README.md](evaluation/README.md).

## My contribution

**Shriyansh Tummala — Evaluation and reliability**

- Structured the evaluation strategy into five question categories and five reliability metrics.
- Built a reusable Python evaluation harness for API-based batch testing.
- Defined a JSONL benchmark format covering expected sources, citations, refusal behaviour, and access restrictions.
- Added machine-readable JSON and CSV reports for failure analysis and retrieval comparison.
- Documented how to compare similarity retrieval with MMR using the same benchmark.

No benchmark scores are claimed in this repository until the evaluator is run against a validated environment and dataset.

## Quick start: evaluation

```bash
cd evaluation
python evaluate.py \
  --dataset benchmark.sample.jsonl \
  --endpoint http://localhost:8000/query \
  --output results
```

The endpoint should accept JSON containing `question`, `user_role`, and `retrieval_mode`. Response-field mappings can be changed with command-line options.

## Technology

Python, TypeScript, Phi-3, Ollama, ChromaDB, MiniLM/Sentence Transformers, OCR, REST APIs.

## Team context

This was a four-person academic group project. The underlying ingestion, retrieval, neural, and application modules are collaborative work. The evaluation folder and the documentation of that layer represent Shriyansh's scoped portfolio contribution.

## Responsible use

Do not commit private documents, model weights, local vector databases, environment variables, or generated evaluation results. Respect the licences and attribution requirements of all datasets, models, and third-party libraries.
