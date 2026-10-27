# Performance and consistency benchmark

`benchmark.py` times the real grading pipeline (`run_grading_job`, the same code the
web interface runs) on a throwaway database, using an instructor's saved provider
settings. Each run is saved as JSON under `results/`.

```
python benchmark/benchmark.py                      # 10, 50 and 100 responses
python benchmark/benchmark.py --sizes 100 200
GRADING_BATCH_SIZE=1 python benchmark/benchmark.py --sizes 24
```

The responses are the 12 synthetic samples in `sample_data/`, repeated with fresh
student IDs. Because each answer appears several times, in different requests, the
run also measures consistency: whether identical answers receive identical scores.

## Results, 27 October 2026

Provider: Google Gemini, `gemini-flash-lite-latest`, free tier. Batch size 10.

| Responses | Time | Per response | Graded | Failed |
|---:|---:|---:|---:|---:|
| 10 | 3.5 s | 0.35 s | 10 | 0 |
| 50 | 16.9 s | 0.34 s | 50 | 0 |
| 100 | 34.0 s | 0.34 s | 100 | 0 |
| 200 | 74.6 s | 0.37 s | 200 | 0 |

**Target of 100 responses in under two minutes: met, at 34 s.** Time grows linearly
with class size. Repeat runs gave 37.3 s and 33.1 s for 100 responses.

## Consistency finding

| Batch size | Repeated answers with identical scores | Largest spread |
|---:|---:|---:|
| 10 | 2 of 12 | 2 marks of 10 |
| 1 | 7 of 8 | 1 mark of 10 |

With ten answers per request, the same answer can receive a score up to 2 marks
different depending on which other answers share its request. Grading one answer per
request removes most of that variation, but on the free tier it reached the rate
limit after about 20 requests (the job stopped cleanly and kept the uploaded data, as
designed). Lowering temperature from 0.2 to 0 made no measurable difference.

So batching is what keeps grading fast and inside the free tier, and it costs
consistency. Reducing this effect, without giving up batching, is part of the
accuracy work that follows.
