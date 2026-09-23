
# Philo Carpenter's South Water Street Store — research dossier

**Record:** `data/structures/carpenter_south_water_store.json` · **Scene status:** standing and
two years old on 1835-07-01 · **South Water Street parcel**

The other half of the Carpenter problem, and **the record that makes `philo_carpenter_log_shop`
doubtful**.

## 1. What is documented

Andreas: in the **summer of 1833** Carpenter *"purchased a lot on South Water Street, between
LaSalle and Wells streets"* and *"erected a small store."* His trade is corroborated
contemporaneously by his own advertisement in *The Chicago Democrat* of 26 November 1833 — drugs,
medicines, oils, paints, dye-stuffs, and also dry groceries, glass and nails — three months after
he built this store. **That advertisement carries no address**, so it names the trade with
certainty and the building not at all.

## 2. The uncertainty is anisotropic, and the along-street half is the big one

The block face is documented and 123 m long — about seven of the street's documented 55 ft lots.
The record sits at the **middle of it**, which is a convention and not evidence.

- across the street: about **20 m**, the georeference's residual;
- **along** the street: about **60 m**.

The **side** of the street is reasoned rather than guessed: the north side of South Water was the
river bank, wharves and landings, and a purchased **lot** with a store erected on it is a
south-side lot.

## 3. The one hesitation about construction

Carpenter's **first** shop is documented as **log**, so he was a man who had built in log once.
Frame is adopted here because this is new work erected on a purchased lot on the business street in
the summer of 1833, when frame was taking over there. **If this building was log it belongs on the
`log_dwelling` archetype**, which is a bigger correction than a repaint.

## 4. What "small" bought

`footprint` is `conjectural` but it is invented *inside the one adjective the source offers*:
7.62 x 6.096 m = **25 x 20 ft**, less than half the documented 55 ft lot width, on a street of
40 ft frontages. `stories` is `inferred` at 1 from the same adjective — Andreas describes Peck's
store by its **storeys** and this one by its **size**, and that contrast is the argument.

## 5. Open threads

An 1834-35 Carpenter advertisement carrying an address would fix the lot **and**, if it named a
cross street, would help settle whether the Lake Street log shop was still in use. The 1834-35 town
lot records for the South Water frontage between Wells and LaSalle would fix the lot outright.

## The parcel's shared inventions

Three things are true of every record in the South Water Street parcel and are written once here
rather than sixteen times:

1. **The borrowed rectangle.** No period map this project has georeferenced shows a building
   footprint, and no source gives a South Water or Lake Street commercial building a dimension
   except Hogan's store (45 x 20 ft) and Philo Carpenter's log shop (16 x 20 ft). Every other
   footprint in the parcel is a rectangle built from figures borrowed from the dataset's own
   attested buildings — 40 ft frontage (Green Tree Tavern, Western Hotel), 25 ft depth (derived
   from the Green Tree's room module), 20 ft depth (Hogan's store) — capped by Andreas's
   documented **55 ft South Water lot width**. The repetition is the admission.
2. **The position method.** Modern intersection centres read from OpenStreetMap at EPSG:26916 on
   2026-08-11, offset 12.2 m (half an 80 ft platted street) to the kerb. South Water Street is
   today's Wacker Drive along the south bank; Wacker was built on its right of way in 1924-26 and
   widened northward over the old dock line, so the two lines are close but not identical.
   Working uncertainty is about **20 m** — the georeference's own residual (17.5 m RMS on Wright
   1834, 3.7 per cent paper stretch) — plus whatever the source's own vagueness adds, which is
   stated per record.
3. **The ground is not there.** Everything in this parcel east of about local E +320 stands
   outside the committed `e1834_harbor_cut` terrain box and is declared
   `ground_contact: outside_modelled_ground`. That is a terrain gap, not a structure gap.
