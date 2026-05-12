# Dataset Inspection Report — Cognition Stress Validation

## 1. Overview
This report documents the inspection of the available cognition datasets for Phase B.5 stress validation. The focus is on their structure, chronology, and suitability for benchmarking the MemLayer runtime.

## 2. LoCoMo Dataset (`locomo10.json`)

### 2.1. Dataset Structure
- **Format**: JSON
- **Organization**: List of conversation samples (`sample_id`).
- **Core Keys**:
    - `conversation`: Multi-session dialogue data.
    - `session_summary`: High-level summaries of each session.
    - `qa`: Ground truth question-answer pairs for evaluation.
    - `event_summary`: Longitudinal summary of the entire timeline.

### 2.2. Conversation Schema (per Sample)
- **Speakers**: `speaker_a`, `speaker_b`.
- **Sessions**: `session_1`, `session_2`, ..., `session_N`.
- **Chronology**: `session_X_date_time` (e.g., "1:56 pm on 8 May, 2023").
- **Utterances**: Each session contains a list of turns with `speaker`, `dia_id`, and `text`.

### 2.3. Statistics (conv-1 example)
- **Total Sessions**: 19.
- **Timeline Span**: May 2023 to October 2023 (~5 months).
- **Avg Turns per Session**: 10-15.
- **Suitability**: Excellent for **Longitudinal Stress Testing**, lineage growth, and semantic continuity validation.

## 3. MSC (Multi-Session Conversation) Dataset

### 3.1. Dataset Structure
- **Format**: Parquet (via symlinks in `Dataset/data/`).
- **Files**: `train`, `test`, `validation`.
- **Current Status**: **BLOCKED**. The symlinks in `Dataset/data/` point to `../../../blobs/`, which appears to be outside the accessible workspace or missing.
- **Suitability**: Designed for **High-Concurrency Stress Testing** and vector scaling, assuming the source data can be recovered.

## 4. Chronology & Metadata Characteristics
- **LoCoMo**: High chronological fidelity. Timestamps are provided as natural language strings, requiring normalization for the `SemanticLineage` engine.
- **Semantic Continuity**: The dialogues show deep semantic persistence (e.g., mentioning events from months prior), making it ideal for testing the **Adaptive Assembly Pipeline**.

## 5. Next Steps
1.  Finalize **Dataset Runtime Mapping** for LoCoMo.
2.  Attempt to resolve the MSC symlink issue to enable concurrency testing.
3.  Design a synthetic "Concurrency Storm" generator using LoCoMo content if MSC remains inaccessible.
