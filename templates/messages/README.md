# Review-request messages: read this first

**Who sends these:** the **owner** (or their staff), to their **own** customers, after a **real visit**, from
the business's own phone or email. We (the operator and the agents) never send them, never receive
customer lists and never store customer names, numbers or emails (docs/11 §2, PIPEDA).

**Same request to everyone.** Every customer gets the same message: no picking happy customers first,
no "if you're unhappy, tell us instead", no asking for a particular star rating (ranking-rules hard
limits 5–6). Reviews from staff, family or friends are not allowed (hard limit 4).

**No incentives.** No discounts, draws, freebies or "thank-you gifts" for reviews (hard limit 5;
Competition Act).

**CASL (Canada's anti-spam law).** A one-off thank-you/review request to a customer who just visited is a
follow-up to that visit. Keep it short, identify the business, and don't add promotions. Anything
promotional (offers, newsletters) needs the customer's consent and an unsubscribe option. Ask the owner to
confirm they're comfortable with this; when in doubt, use the printed card and the counter script instead.

Placeholders filled by `tools/review_card.py`: `{business_name}`, `{review_link}`.
`{first_name}` is filled by the owner when sending (or the greeting is dropped).

Files: `sms.txt`, `whatsapp.txt`, `email.txt`, `counter-script.md`, `how-to-get-review-link.md`.
