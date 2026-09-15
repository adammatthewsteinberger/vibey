---
name: foodenv-food-safety-and-food-service
description: "Use when food safety or commercial food service is the question: pathogens and the temperature thresholds that actually control them, time-temperature control and the danger zone, HACCP and how a plan is built, cross-contamination and allergen control, kitchen organization and station design, restaurant economics, menu engineering, and regulation and inspection. The temperature and holding thresholds are the operative safety content, not general guidance."
---

# Cooking, Cleaning and Waste Sciences: Food Safety, HACCP, and Running a Kitchen

> **Part 2 of 5** of the *Cooking, Cleaning and Waste Sciences* reference (plugin `cooking-cleaning-waste-sciences`), covering §12–§18. Sibling skills: `foodenv-food-science` (§0–§11), `foodenv-cleaning-chemistry` (§19–§23), `foodenv-wastewater-and-waste-management` (§24–§28), `foodenv-reference` (§29–§34). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry and the food-safety thresholds are settled. Two areas are live. See §29 → `foodenv-reference` for recycling economics and EPR, and PFAS in biosolids.

> **⚠️ One domain, three stages: transform the food, clean up after it, deal with what's
> left.** **Complements an agriculture reference (where the food comes from) and a
> chemistry reference (the underlying reactions).**
>
> **⚠️ Two safety items stated up front, because both can kill and both are common:**
> - ⚠️ **NEVER mix bleach with ammonia, or bleach with acids** (§22 → `foodenv-cleaning-chemistry`). **These produce
>   toxic gases in ordinary domestic quantities.**
> - ⚠️ **The food-safety temperatures in §12 are not suggestions.** **They are the output
>   of pathogen destruction curves.**
>
> **⚠️ GOTCHA** boxes mark folklore that is wrong, and things that hurt people.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Cooking is heat transfer plus chemistry, and almost every technique question is
>    really a heat-transfer question** (§2 → `foodenv-food-science`). **Understanding that replaces a hundred
>    memorized rules.**
> 2. **⚠️ Cleaning is chemistry matched to soil type** (§20–§21 → `foodenv-cleaning-chemistry`). **"Stronger cleaner"
>    is usually the wrong answer; "right chemistry" is usually the right one.**
> 3. **⚠️ The waste hierarchy is ordered by actual impact, and public attention is
>    inverted relative to it** (§25 → `foodenv-wastewater-and-waste-management`). **Recycling gets the attention; reduction and reuse
>    do the work.**

---

## §12. ⚠️ Pathogens and Temperature

> **⚠️ These numbers are the output of pathogen destruction curves and they are not
> negotiable.**

```
⚠️ DANGER ZONE      40–140°F / 4–60°C. Rapid bacterial growth
⚠️ TWO-HOUR RULE    max 2 hours in the danger zone cumulative
                    (⚠️ ONE hour above 90°F/32°C)
⚠️ COOKING TEMPERATURES (US FDA guidance, internal)
   Poultry, stuffed foods, leftovers, casseroles   ⚠️ 165°F / 74°C
   Ground meat (beef, pork, lamb)                  ⚠️ 160°F / 71°C
   Whole-muscle beef/pork/lamb, fish               ⚠️ 145°F / 63°C + 3 min rest
   Eggs                                            cook until firm
⚠️ COOLING (the most-violated rule)  135°F→70°F within 2 hours,
   then 70°F→41°F within 4 more. ⚠️ Total 6 hours
⚠️ REHEATING        to 165°F / 74°C
⚠️ HOLDING          hot ≥135°F / cold ≤41°F
```
**⚠️ Time AND temperature are interchangeable, which is the sous-vide insight**:
⚠️ **poultry held at 145°F for long enough achieves the same log reduction as an instant
165°F** — **pasteurization is a curve, not a threshold.** **⚠️ But the tables matter: use
published time-temperature tables, not guesswork.**
**⚠️ The major pathogens and their signatures**: **Salmonella (poultry, eggs), *E. coli*
O157:H7 (⚠️ ground beef — why ground meat needs a higher temperature than whole muscle:
surface contamination gets mixed throughout), Listeria (⚠️ grows at refrigeration
temperatures, dangerous in pregnancy), Campylobacter (poultry), *Staph aureus* (⚠️ produces
a HEAT-STABLE TOXIN — reheating does not fix it), *Bacillus cereus* (⚠️ classically
reheated rice), Norovirus (⚠️ the leading cause, and it's spread by infected FOOD HANDLERS
— which is why sick staff must stay home), and *Clostridium botulinum* (§10 → `foodenv-food-science`).**
> **⚠️ GOTCHA — cooling is where most commercial food safety failures actually happen,
> not cooking.** ⚠️ **A large stockpot of stew placed whole in a refrigerator can stay in
> the danger zone for many hours at its centre.** **Divide into shallow pans, use ice
> baths or ice wands, and MEASURE — don't assume.**

---

## §13. HACCP

**⚠️ Hazard Analysis and Critical Control Points — a systematic preventive framework, and
the same logic as the IPM and biosecurity frameworks elsewhere: control the process, not
the outcome.**
```
1. Hazard analysis (biological, chemical, physical)
2. ⚠️ Identify critical control points — where control is ESSENTIAL
3. Establish critical limits (⚠️ the numbers in §12)
4. Monitoring procedures
5. Corrective actions
6. Verification
7. ⚠️ Record keeping — no records means it didn't happen, to an inspector
```
**⚠️ Prerequisite programs matter as much as HACCP itself**: **supplier control, sanitation
standard operating procedures, pest control, personal hygiene, and training.**

---

## §14. Cross-Contamination and Allergens

**⚠️ Separate raw and ready-to-eat: separate boards, separate storage, and ⚠️ store raw
meats BELOW ready-to-eat foods so drips can't contaminate downward.** **Order by cook
temperature: ready-to-eat top, then whole fish, whole cuts, ground meat, poultry lowest.**
**⚠️ Handwashing is the single highest-value intervention** — **20 seconds, soap, warm
water, and it is mechanical removal more than chemical kill.** ⚠️ **Gloves are not a
substitute and create false confidence: contaminated gloves transfer just as well as
contaminated hands.**
**⚠️ Allergens** — **the major declarable allergens vary by jurisdiction but generally
include milk, eggs, fish, crustacean shellfish, tree nuts, peanuts, wheat, soy and (in the
US since 2023) sesame.** ⚠️ **Cross-contact is not cooked away — allergenic proteins
survive heat** — **so allergen protocols mean dedicated equipment and clean surfaces, not
just careful ingredient selection.** **⚠️ Anaphylaxis is a life-threatening emergency and
"a little bit" can trigger it.**
**⚠️ Don't wash raw poultry** — **it aerosolizes contamination around your sink and does
not reduce risk.**

---

# PART III — RESTAURANTS

---

## §15. Kitchen Organization

**⚠️ Mise en place is the organizing discipline** — **everything prepped, measured and
positioned before service, because ⚠️ service has no time for preparation.**
**The brigade system** (Escoffier — chef de cuisine, sous chef, chef de partie roles:
saucier, poissonnier, entremetier, garde manger, pâtissier) ⚠️ **is heavily simplified in
most modern kitchens but the underlying idea — station ownership and clear handoffs —
survives because it works.**
**⚠️ Flow and layout**: **receiving → storage → prep → cooking → plating → service →
dish.** ⚠️ **Cross-traffic between dirty and clean flows is both a safety hazard and a
speed problem** — **the same principle as §14, applied to floor plan.**
**⚠️ The expediter role** is the throughput bottleneck management function (see an
operations reference on constraints): **coordinating tickets so a table's dishes finish
together.**

---

## §16. Restaurant Economics

```
⚠️ PRIME COST = food cost + labour cost. THE number operators run on.
   Commonly targeted around 60–65% of sales; above ~70% is distress
FOOD COST %     ⚠️ typically ~28–35% depending on concept
LABOUR %        ⚠️ typically ~25–35%
OCCUPANCY       rent and utilities, ideally under ~10%
⚠️ NET MARGIN   ⚠️ commonly in the low-to-mid single digits. This is a
   thin-margin business and that fact drives every other decision
```
**⚠️ Why the margins are thin and what follows**: **perishable inventory, unpredictable
demand, high fixed costs, and labour intensity.** ⚠️ **Which is why waste control, portion
control and yield management matter disproportionately** — **a few points of food cost is
the entire net margin.**
**⚠️ Yield and actual food cost**: **the AS-PURCHASED versus EDIBLE-PORTION distinction is
where costing goes wrong.** ⚠️ **A whole fish at $10/lb with 45% yield costs over $22/lb
on the plate**, **and menus priced off purchase cost lose money silently.**
**⚠️ Waste is both a cost and a margin lever**: **over-portioning, spoilage, over-production
and trim.** ⚠️ **Tracking waste by category usually reveals one or two dominant sources
rather than diffuse loss.**

---

## §17. Menu Engineering

**⚠️ Classify every item on two axes: POPULARITY and CONTRIBUTION MARGIN** (⚠️ **margin in
dollars, not food cost percentage — a common and expensive confusion**).
```
STARS      ⚠️ popular + high margin      → protect, feature, don't change
PLOWHORSES popular + low margin          → ⚠️ raise price carefully or re-cost
PUZZLES    unpopular + high margin       → reposition, describe better, or train staff
DOGS       unpopular + low margin        → ⚠️ remove
```
**⚠️ Design levers that measurably affect selection**: **item position (⚠️ eye-tracking
consistently shows top-right and boxed items get more attention), avoiding a price column
(⚠️ which invites price-shopping down the list), descriptive naming, and limiting choice
(⚠️ very long menus increase waste, slow service, and complicate prep).**
**⚠️ Percentage food cost is the wrong optimization target on its own.** ⚠️ **You bank
dollars, not percentages — a 40%-food-cost item with a $14 margin beats a 25% item with a
$4 margin.**

---

## §18. Regulation and Inspection

**⚠️ In the US, the FDA Food Code is a model adopted with variation by states and
localities** — ⚠️ **so your local health department's version is the authority.**
**Typical requirements**: **certified food protection manager, employee health policy
(⚠️ exclusion of ill workers is a Norovirus control, §12), temperature logs, approved
sources, ⚠️ handwashing sinks that are accessible and used only for handwashing, warewashing
sanitizer concentration verified with test strips, and pest control.**
**⚠️ Inspection scores are a snapshot; the compliance that matters is the daily routine.**
**⚠️ The most commonly cited violations cluster around temperature control, handwashing,
and cross-contamination** — **which is to say, §12 and §14.**

---

# PART IV — CLEANING SCIENCE
