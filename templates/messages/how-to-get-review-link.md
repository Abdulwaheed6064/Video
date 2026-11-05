# How to get the short Google review link

The owner (or the operator, with Manager access) copies it from the Google Business Profile:

1. Open the business profile while signed in as an owner or manager (search the business name on Google, or open Google Maps).
2. Find the option to **ask for reviews** (often labelled "Ask for reviews" / "Get more reviews"). The
   wording in the profile editor changes from time to time.
3. Copy the link it shows. It usually looks like `https://g.page/r/XXXXXXXX/review`.
4. Test it on your phone before printing anything.

Then run: `uv run python tools/review_card.py --client <slug> --link "<that link>"`
