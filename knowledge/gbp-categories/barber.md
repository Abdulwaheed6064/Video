# GBP categories: barber shops

> Every category below is **unverified** until the operator has checked it in the GBP category picker
> for this client (the picker's list changes). Record the check in the client's `log.md`.
> Pick categories from what the business really is, then compare with `competitors.json → primary_category`.

Written 2026-11-04 (B05).

## Primary (choose one)

| Candidate | Status | Use when |
| --- | --- | --- |
| Barber shop | unverified | The default for a barber; most likely what the top 3 use |
| Hair salon | unverified | Only if the business presents as a unisex/women's salon rather than a barber |

## Secondary (only if genuinely offered, each backed by a verified `service` fact)

| Candidate | Status | Use when |
| --- | --- | --- |
| Hair salon | unverified | Barber that also does full salon work (colour, styling for all) |
| Men's hair salon (if present in the picker) | unverified | Positioned as men's grooming |
| Beauty salon | unverified | Rarely right; only with verified beauty services |
| Shaving / grooming store-type categories | unverified | Only if it sells grooming products in-store (verified) |

## Do not add

- Categories for services not offered ("Hairdresser" for a pure barber, "Nail salon", "Spa").
- Categories added only to catch a search (that is relevance spam and can trigger a review of the profile).
- More than a handful of secondaries. Every one must be defensible from verified facts.
- Frequent changes: change the primary category at most once per batch, marked `risk: high`.
