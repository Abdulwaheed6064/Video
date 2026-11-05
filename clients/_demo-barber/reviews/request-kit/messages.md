> SYNTHETIC demo kit: fictional business.

# Review request kit: messages

For the **owner** to send to their own customers after a real visit. Same message to everyone; no incentives; no screening. Read `templates/messages/README.md` (CASL note) first.

## SMS

```text
Hi {first_name}, thanks for visiting Demo Fade Co. (fictional) today. Would you leave us a Google review? It takes a minute: https://g.page/r/EXAMPLE/review
```

## WhatsApp

```text
Hi {first_name}, thanks for coming in to Demo Fade Co. (fictional). Would you leave us a Google review? Here's the link: https://g.page/r/EXAMPLE/review
```

## Email

```text
Subject: Thanks for visiting Demo Fade Co. (fictional)

Hi {first_name},

Thanks for visiting Demo Fade Co. (fictional). Would you leave us a Google review? It helps people nearby find us.

https://g.page/r/EXAMPLE/review

Thanks,
Demo Fade Co. (fictional)
```

## 30-second counter script (for the owner and staff)

Say this to **every** customer at the end of the visit, the same way each time:

> "Thanks for coming in. If you have a minute, would you leave us a Google review? The QR code's
> right here, or I can text you the link."

Then point to the card at the till. That's it.

Don't:
- choose who to ask, or ask only customers who seem pleased;
- ask for a particular rating;
- give anything in return for a review, of any kind;
- ask friends, family or staff to post reviews;
- write or post a review on someone's behalf, or on their phone.

## How to get the short Google review link

The owner (or the operator, with Manager access) copies it from the Google Business Profile:

1. Open the business profile while signed in as an owner or manager (search the business name on Google, or open Google Maps).
2. Find the option to **ask for reviews** (often labelled "Ask for reviews" / "Get more reviews"). The
   wording in the profile editor changes from time to time.
3. Copy the link it shows. It usually looks like `https://g.page/r/XXXXXXXX/review`.
4. Test it on your phone before printing anything.

Then run: `uv run python tools/review_card.py --client <slug> --link "<that link>"`

