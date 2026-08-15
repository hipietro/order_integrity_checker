# Suggested Fixes for Invalid Orders

The order integrity workflow provides actionable suggestions alongside validation errors so users can understand how an invalid CSV row can be corrected without the application changing data automatically.

## Supported suggestions

The suggestion engine currently covers:

- **Order codes:** safely normalizes numeric and `ORD`-style values, for example `ord-7` to `ORD007`.
- **Statuses:** proposes the closest supported status when a likely typo is detected, for example `pendng` to `pending`.
- **Customer names:** recommends removing leading, trailing, and repeated spaces.
- **Quantities:** flags zero and negative quantities for review and warns when a quantity is unusually high.

Suggestions are advisory only. The application does not silently rewrite invalid source data.

## Validation and preview flow

`validator.validate_all_csv_orders()` keeps a copy of the raw CSV row before normalization, validates the normalized order, and generates suggestions from the original values and validation errors.

The service layer preserves those suggestions while quality scores are added. `build_csv_import_preview()` then exposes them on every skipped order and also returns:

- `suggestion_count`: total number of generated suggestions in the preview.
- `orders_with_suggestions`: number of orders that have at least one suggestion.

This keeps suggested fixes available to CLI, GUI, and future API presentation layers without duplicating business rules.

## Invalid-order report

`generate_invalid_orders_report()` writes suggestions directly below the validation errors for each invalid order. A `Suggestions:` section is emitted only when at least one actionable fix is available.

Example:

```text
Order code: ORD007
Customer name: Mario Rossi
Quantity: 0
Status: pendng
Errors:
- quantity must be greater than zero
- invalid status
Suggestions:
- Review quantity: it must be greater than zero
- Did you mean status: pending?
```

## Testing

Automated coverage includes:

- safe order-code normalization suggestions;
- closest-status suggestions;
- customer-name whitespace suggestions;
- zero, negative, and unusually high quantity review suggestions;
- preservation of suggestions through preview and import services;
- preview suggestion summary counts;
- invalid-order report output with and without suggestions.

The tests are intentionally separated between unit-level suggestion generation and integration-level service/report behavior so changes to presentation code do not require duplicating the suggestion rules.
