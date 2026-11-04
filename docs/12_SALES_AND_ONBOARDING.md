# Sales and onboarding

## 1. Getting the first clients

1. **Case study first.** Run the sprint on one friendly business (friend, family, a barber you use) for free
   or the pilot price. Written permission, Manager access, real baseline. This becomes your proof.
2. **Walk-in with a rank map.** Pick 20 businesses in Bradford, Newmarket, Aurora, East Gwillimbury where
   the free audit (07 §6) shows they're missing from the 3-pack near their own shop. Print the one-page map.
   Walk in at a quiet time (barbers: weekday mid-morning). In-person avoids most CASL issues with cold email.
3. **Local groups:** chamber of commerce events, BIA meetings, local business Facebook groups (follow their
   rules on promotion).
4. **Referrals:** offer existing clients a month free for a referral that signs (that's fine — it's not a
   review incentive).

Track in `prospects/pipeline.csv`: business, town, niche, date, audit sent, reaction, objection, next step.

Target: 20 audits → 10 conversations → 4 serious → 2 paid pilots. If 10 conversations produce nothing,
change the niche/offer before building more features.

## 2. The pitch (2 minutes, with the printed map)

> "I checked how you show up on Google Maps when someone near your shop searches 'barber Bradford'.
> Green is where you're in the top 3, red is where you're not. Right now you're top 3 here and here —
> and invisible across most of town, even 500 metres from your door.
>
> These three shops beat you mostly because of [category / reviews / website page] — here's the list.
>
> I fix all of it in 20 days: your Google profile, a proper page for your services, your listings across
> the main directories, and a simple way to get more reviews from your real customers. On day 20 I re-run
> this exact map so you see what changed.
>
> My target is top 3 within about [3 km] for your main searches. If your map hasn't improved by day 30,
> your first month is free. Setup is $750, then $249 a month."

Don't say: "guaranteed #1", "everyone in Toronto", "Google partner", "I know someone at Google", "AI will
do your marketing".

Common objections:

| Objection | Answer |
| --- | --- |
| "I already rank" | "Here — on this map — you rank in 6 of 49 spots. Want the other 43?" |
| "Another SEO guy promised #1 and nothing happened" | "That's why I show you the map before and after, and why my guarantee is about measurable movement, not a promise nobody can keep." |
| "Too expensive" | "One new regular is worth ~$450 a year. You need less than one a month to cover it." / Offer pilot price only if you still need case studies |
| "Can you just do reviews?" | "Reviews alone help, but your category and page are holding you back — the bundle is what moves the map." |

## 3. Onboarding checklist (day 0)

**Before the call**
- [ ] Agreement signed (11 §3), 50% setup paid
- [ ] `clients/<slug>/` created in pilot/production mode; baseline scheduled for day 1

**On the call (45 min)**
- [ ] GBP: owner adds you as **Manager** (Business Profile → Settings → People and access). Never take passwords
- [ ] Is the profile verified? Any suspensions or pending edits? Who else has access?
- [ ] Storefront, service-area or hybrid? If SAB: is the address hidden?
- [ ] Website: who controls domain/DNS and hosting? Add you as a user, or plan a new site on their domain
- [ ] Search Console: add you as user, or set up together
- [ ] Facts: services (in customer words), prices policy, hours + holiday hours, phone, booking link,
      payment methods, languages, parking, accessibility, year founded, licences, team first names (consent)
- [ ] Photos: ask for 10+ real ones now; agree a photo day
- [ ] Reviews: explain the rules (ask everyone, no incentives, no family/staff reviews); agree who asks and when
- [ ] Their numbers: average ticket, how many new customers they can handle
- [ ] Preferred channel and turnaround for approvals (e.g. WhatsApp, same day)

**After the call**
- [ ] Run intake agent → send 1-page fact sheet for "confirmed"
- [ ] Book day-20 review call now

## 4. Monthly client communication

- Week 1: WhatsApp summary (3 lines + 1 heatmap).
- Month end: 1-page report.
- Quarterly: 15-min call — results, next quarter's focus, price review.

## 5. Offboarding

Remove yourself as Manager when asked; export the client folder (facts, site source, reports, citations
plan) to the owner; transfer the Cloudflare project or hand over the static build; delete the client folder
within 30 days; note it in `DECISIONS.md`.
