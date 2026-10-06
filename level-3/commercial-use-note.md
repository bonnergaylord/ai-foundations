# What would make this commercial rather than coursework

Today this is coursework. Nobody pays for it, no business relies on it, it serves a
250-record sample, and it runs on free plans. I read the terms of the four parties
involved on 2026-10-05. Each one draws the line in a different place.

## GitHub Pages, which hosts the page

The page could not stay on Pages as a product. GitHub's limits page says Pages is "not
intended for or allowed to be used as a free web-hosting service to run your online
business, e-commerce site, or any other website that is primarily directed at either
facilitating commercial transactions or providing commercial software as a service
(SaaS)."

A free lookup page is fine. Charging for lookups, or running it as a firm's tool, is
the SaaS case the terms name. It would need to move to a host whose terms allow that.
Pages also says it "shouldn't be used for sensitive transactions like sending passwords
or credit card numbers."

Source: docs.github.com, "GitHub Pages limits".

## Cloudflare Workers and D1, which host the API and the database

The free plan does not forbid commercial use. The Self-Serve Subscription Agreement
covers free plans, contemplates use "on behalf of a company", and I found no
non-commercial clause in it. Two things would change at business scale:

- **No guarantee.** For free services, "We will have no liability for any harm or damage
  arising out of or in connection with any Free Services." A business relying on this
  takes that risk.
- **Hard daily caps.** Workers Free allows 100,000 requests a day. D1 Free allows
  5 million rows read a day. Past the cap, D1 returns errors and the lookup goes dark
  until midnight UTC.

The "parcels over an acre" endpoint reads about a hundred rows per call even with its
index, so one busy integration could use up the read cap. Commercial use means moving to the paid plan.

Sources: cloudflare.com/terms; developers.cloudflare.com, Workers limits and D1 pricing
pages.

## Anthropic, whose Claude reads the data through the connector

On a personal plan (Free, Pro or Max), Claude is governed by the Consumer Terms. Three points matter:

- **Evaluation use is personal only.** The Consumer Terms say evaluation use is "for
  your personal, non-commercial use only".
- **My plan can't serve other people.** The Claude Code legal page says developers may
  not "route requests through Free, Pro, or Max plan credentials on behalf of their
  users."
- **Inputs may be used for training.** Consumer inputs may be used for training unless
  you opt out.

If coworkers or customers used this connector through Claude, it would need to run
under the Commercial Terms: a Team or Enterprise plan, or the API. Under those terms,
"Anthropic may not train models on Customer Content." That is the version a firm's IT
department would require.

If owner names were added, the Usage Policy's privacy rules would also apply. It bars
"sharing personal information without consent" and tracking a person's location. That
is a design constraint, not just a terms question.

Sources: anthropic.com/legal/consumer-terms, /commercial-terms, /aup;
code.claude.com/docs/en/legal-and-compliance.

## Wake County, which publishes the parcel data

The county's Parcels dataset on its open-data portal is licensed CC BY 4.0. That permits
commercial reuse with attribution, so the data itself is the least restrictive part of
the stack. A commercial version would need three things:

- **Attribution:** credit Wake County GIS visibly, which the page does not yet do.
- **Its own disclaimer:** carry the county's disclaimer, that the data "cannot be
  construed to be a legal document" and that primary sources "must be consulted for
  verification". Nobody should treat a lookup as a title search.
- **A refresh process:** the sample is a fixed snapshot, and live county data changes
  daily.

I could not find a written county policy on owner names or bulk download. The live
parcel layer does publish owner and mailing-address fields. Before a commercial version
showed owners, I would get that answer in writing, from the county and from counsel, on
North Carolina public-records law.

Sources: Wake County's Parcels item on its ArcGIS open-data portal (data.wake.gov); the
catalog.data.gov "Parcels" record; wake.gov iMAPS information page.

## The short answer

It turns commercial the moment any of these is true:
- someone pays for it;
- a business depends on it;
- Claude answers other people through it; or
- it serves the full county dataset with owner names.

The changes that would follow:

| Part | Change |
| --- | --- |
| Page | Off GitHub Pages, onto a host that allows commercial use |
| API and database | Onto Cloudflare's paid plan |
| Claude | Onto Commercial Terms (Team or Enterprise plan, or the API) |
| Data | Add Wake County attribution and the county's disclaimer, put a refresh process in place, and get written guidance before showing owner names |

None of this is legal advice. I would bring this note to counsel before charging anyone.
