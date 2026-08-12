# Order quality scoring

The order quality score is an explainable review signal from **0 to 100**.

It does not replace order validation. Validation decides whether an incoming order can be imported. Quality scoring answers a different question: how trustworthy and ordinary does the order look?

A technically valid order can therefore be imported while still receiving a medium score and a recommendation for manual review.

## Score bands

- **85-100 — high:** no meaningful quality concerns were detected.
- **60-84 — medium:** the order is usable but contains one or more signals worth reviewing.
- **0-59 — low:** several strong data-quality or validation problems are present.

Scores are clamped at zero.

## Signals

The scorer currently considers:

- validation failures such as missing fields, duplicated codes and invalid statuses
- suspicious duplicate matches produced by `duplicate_detector.py`
- unusually high quantities
- missing, very short or generic customer names
- unsupported statuses

Every deduction is returned as a structured penalty containing a code, point value and human-readable explanation.

## Quantity heuristic

The current project does not yet have product-specific quantity distributions, so quantity scoring intentionally uses simple deterministic thresholds:

- over 100 units: -10
- over 500 units: -18
- over 1000 units: -25

These are review heuristics, not business rules. They can later be replaced by customer- or product-specific baselines without changing the CLI or GUI contract.

## Customer-name heuristic

Names such as `Customer`, `Client`, `Unknown`, `Test` and similar placeholder values are considered generic and receive a penalty even when they are technically long enough to pass basic validation.

Very short but valid names also receive a smaller penalty.

## Duplicate signal

Suspicious duplicate detection is reused rather than reimplemented inside the scorer.

The first suspicious duplicate reduces the score by 20 points. Additional matches add smaller penalties, capped at 35 points for the duplicate signal.

The order is still not automatically rejected. The score sets `review_recommended` and keeps all duplicate matches available for inspection.

## CSV preview flow

`services.preview_csv_import()` now:

1. validates every CSV order
2. loads existing database orders
3. compares each CSV row with existing orders and the other incoming rows
4. calculates one quality object per order
5. passes the scored validation results to the reusable preview builder

The preview also exposes:

- `average_quality_score`
- `review_recommended_orders`

Both CLI and GUI read these values from the same preview object.

## Stored order details

The unified order detail service also calculates the quality score for an existing order. The GUI displays this score inside `Integrity insights` together with suspicious duplicate information.

This keeps the scoring logic reusable across presentation layers and prepares it for the future REST API.
