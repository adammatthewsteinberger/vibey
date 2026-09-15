---
name: music-reference
description: "Use when checking what is live (AI music licensing and litigation with a fair-use ruling still pending, and streaming economics, verified August 2026), correcting a music-theory misconception, finding the books, or needing a picker and the numbers worth holding. Companion to the other music-theory-fundamentals skills."
---

# Music Theory Fundamentals: What's Live, Misconceptions, and Canon

> **Part 5 of 5** of the *Music Theory Fundamentals* reference (plugin `music-theory-fundamentals`), covering §22–§26. Sibling skills: `music-claims-harmonic-series-psychoacoustics-and-tuning` (§0–§4), `music-pitch-scales-rhythm-timbre-and-chords` (§5–§9), `music-functional-harmony-counterpoint-and-form` (§10–§14), `music-analysis-jazz-popular-non-western-and-meaning` (§15–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The theory is centuries stable. Two areas are live. See §22 below for AI music licensing and litigation, and streaming economics.

> **⚠️ Read §1 → `music-claims-harmonic-series-psychoacoustics-and-tuning` first.** **"Music theory" names three different things stacked on top of
> each other**, **and the discipline's biggest failure mode is presenting the third as
> though it were the first.**
>
> **⚠️ GOTCHA** boxes mark things taught confidently that are either false, or true only
> of one repertoire.
>
> **The three ideas that organize this document:**
> 1. **⚠️ There is a real physical substrate — the harmonic series — and it genuinely
>    constrains what sounds consonant** (§2–§3 → `music-claims-harmonic-series-psychoacoustics-and-tuning`). **This is more than art theory has, and
>    it is far less than "music theory is physics."**
> 2. **⚠️ What is taught as "music theory" is overwhelmingly the grammar of European
>    common-practice tonality, roughly 1650–1900.** **It's a superb description of a
>    specific repertoire.** ⚠️ **It systematically mis-describes jazz, most popular music,
>    and nearly all non-Western music** (§17–§19 → `music-analysis-jazz-popular-non-western-and-meaning`).
> 3. **⚠️ Theory is descriptive, not prescriptive — it was reverse-engineered from music
>    that already existed.** **"You can't use parallel fifths" means "Bach didn't, in this
>    genre, for these reasons."** **Debussy used them constantly.**

---

## §22. What's Live — verified August 2026

### 22.1 ⚠️ AI music: from lawsuits to licensing, with a fair-use ruling still pending
**⚠️ This moved further and faster than the equivalent situation in visual art, and it
moved in a direction that surprised people: toward licensing deals rather than judgments.**

**The sequence:**
- **⚠️ June 2024: the RIAA, on behalf of all three majors (UMG, Sony, Warner), sued Suno
  and Udio for mass copyright infringement over training on copyrighted recordings.**
  **Suno and Udio argued fair use.**
- **⚠️ October 2025: UMG settled with Udio**, bundled with a licensing deal for a licensed
  AI platform.
- **⚠️ November 2025: Warner settled with BOTH Udio and Suno.** **The Suno deal (announced
  25 November) requires Suno to launch licensed models replacing its current ones in 2026,
  and to implement download restrictions.**
- **⚠️ Sony did not settle with either, and UMG continued against Suno.**

> **⚠️ GOTCHA — the settlements did not resolve the legal question, and the critique of
> them is worth taking seriously.** ⚠️ **One framing that recurs: the pattern is "launch,
> train, settle" — operate on copyrighted material without permission, face suits only
> from those powerful enough to sue, then legitimize through selective licensing while
> everyone else's work remains in the training data uncompensated.** **Major labels
> negotiated direct licenses; independent artists have no licensing pathway and are
> pursuing class actions.** ⚠️ **This mirrors the early streaming era's power imbalance
> closely enough that the comparison is being made explicitly.**

**⚠️ What is still genuinely undecided as of mid-2026:**
- **⚠️ A summary-judgment hearing in the Massachusetts Suno case was scheduled for July
  2026**, **with discovery reportedly showing audio fingerprinting identified millions of
  copyrighted recordings in the training data.** ⚠️ **The stakes are described plainly:
  if Suno wins on fair use, it validates train-first-license-later and undercuts every
  licensing deal; if it loses, the settlement template becomes the industry standard.**
  **Reporting differs on timing — at least one tracker suggests court schedules push a US
  fair-use ruling into 2027** — ⚠️ **so treat the date, not the substance, as uncertain.**
- **⚠️ An inversion nobody predicted: in July 2026 the American Federation of Musicians
  reportedly sued Universal and Warner — not the AI companies — alleging that session
  recordings by its members were licensed for AI training without the consent or
  compensation their collective bargaining agreement requires.** ⚠️ **The plaintiffs
  became defendants.** **Worth flagging as reported and worth verifying.**
- **⚠️ Not globally harmonized.** **In November 2025 the Munich Regional Court largely
  ruled for GEMA, finding that memorization and reproduction of German song lyrics
  infringed and that the text-and-data-mining exception did not cover it** — **a European
  outcome pointing the other way from the US fair-use argument.**

**⚠️ Practical note for anyone using these tools**: **commercial rights granted by a
platform's terms are NOT the same thing as copyright a court would recognize** — ⚠️ **and
per the visual-art parallel, US law requires human authorship** (see an art theory
reference §23.1).

### 22.2 ⚠️ Streaming economics — and a supply/demand gap that inverts the panic
**⚠️ This is the context in which music actually gets made now, and one widely-repeated
alarming statistic turns out to mean something quite different from what it's used for.**

**⚠️ Per-stream rates, reported for 2026 — approximate, and they vary enormously by
listener country and free/premium mix:**
```
Tidal        ~$0.012–0.015    Apple Music  ~$0.006–0.010
Deezer       ~$0.0064         Amazon       ~$0.004
Spotify      ⚠️ ~$0.003–0.005  YouTube Music ~$0.002–0.008
⚠️ Overall range reported at roughly $0.0007 to $0.015 — a 15x-plus spread
⚠️ At Spotify rates, roughly 20–33 MILLION streams to gross $100,000
```
**⚠️ Structural features that matter more than the rate:**
- **⚠️ PRO-RATA POOLS.** **Most platforms pay a share of a pool based on share of total
  streams, not a price per play.** ⚠️ **Your subscription doesn't go to the artists you
  listen to — it goes into a pot divided by everyone's listening.** **Deezer's ACPS and
  SoundCloud's fan-powered model are attempts to change this.**
- **⚠️ Spotify's 1,000-stream threshold (since April 2024)**: **tracks below it earn
  nothing.** **Reported to have reallocated ~$40M/year into the eligible pool** — ⚠️ **and
  with 200M+ tracks on the platform, an estimated 87% fall short of that mark.**
- **From January 2026, US songwriters receive 15.3% of streaming service revenue**, up
  0.75 points.
- **⚠️ Price rises grow the pool but not individual earnings**, **unless your share of
  listening holds — Spotify payouts rose from ~$10bn (2024) to ~$11bn (2025).**

> **⚠️ GOTCHA — "AI is flooding streaming" is true about UPLOADS and false about
> LISTENING, and the gap is the whole story.** ⚠️ **Deezer — the only major platform
> publishing both figures, which is itself informative — reported roughly 75,000 fully
> AI-generated tracks uploaded daily by April 2026, about 44% of daily uploads, passing
> 50% by June.** **The trajectory ran from ~10K/day in January 2025.**
> **⚠️ But AI tracks account for only 1–3% of streams, and Deezer reports up to 85% of the
> streams they do get are detected as fraudulent and stripped from royalty payments.**
> ⚠️ **Strip the fraud and genuine listening to AI music sits under half a percent.**
> **The supply share is running something like 15–44x the consumption share.**
>
> **⚠️ So the honest reading: this is a fraud and distribution problem, not a
> displacement-of-human-music problem.** **The dominant economic use of AI tracks so far
> is generating stream-farm royalty claims that platforms then detect and demonetize** —
> **a North Carolina man pleaded guilty to an $8 million streaming fraud using AI-generated
> tracks and bots.** ⚠️ **The real mechanism of harm is dilution of a fixed pool by
> near-zero-cost supply, not listeners choosing synthetic music.**

**⚠️ And note the structural point underneath**: **because platforms pay a fixed share of
a pool rather than per unit, extra content dilutes the humans in the pool and costs the
platform nothing either way.** ⚠️ **Which is why supply-side cleanup — Spotify reported
removing 75+ million spammy tracks — doesn't by itself change the incentive that produced
the supply.**

---

## §23. Misconceptions

| Misconception | Correction |
|---|---|
| Music theory is the rules of music | ⚠️ **Descriptive grammar of one repertoire** (§1 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| Western tonality reflects natural law | ⚠️ **Octave and fifth have acoustic basis; the rest is culture** (§1 → `music-claims-harmonic-series-psychoacoustics-and-tuning`, §2 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| The minor triad is in the harmonic series like the major | ⚠️ **It isn't; the "undertone series" has no acoustic basis** (§2 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| Dissonance is objective | ⚠️ **Sensory roughness is; musical dissonance is learned** (§3 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| Equal temperament is "in tune" | ⚠️ **Every major third is ~14 cents sharp** (§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| "Well-tempered" means equal-tempered | ⚠️ **It means all keys usable, each with distinct colour** (§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| Keys have inherent character | ⚠️ **They did under unequal temperament. 12-TET removed the cause** (§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| We could tune perfectly with better engineering | ⚠️ **Powers of 3 are never powers of 2. It's arithmetic** (§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| A♯ and B♭ are the same note | ⚠️ **Only in equal temperament, and never functionally** (§5 → `music-pitch-scales-rhythm-timbre-and-chords`) |
| Modes are white notes from different starting points | ⚠️ **A mode needs a tonic actually established** (§6 → `music-pitch-scales-rhythm-timbre-and-chords`) |
| Parallel fifths are forbidden | ⚠️ **They collapse two voices into one — sometimes that's the goal** (§10 → `music-functional-harmony-counterpoint-and-form`) |
| Bach thought in chord progressions | ⚠️ **Figured bass and lines; "chord" is a later abstraction** (§9 → `music-pitch-scales-rhythm-timbre-and-chords`, §13 → `music-functional-harmony-counterpoint-and-form`) |
| Sonata form is about themes | ⚠️ **It's a key drama first** (§14 → `music-functional-harmony-counterpoint-and-form`) |
| Pop music is harmonically simple | ⚠️ **Wrong analytical tool. Content is in timbre, groove, production** (§18 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| The ♭VII in rock is a weakened dominant | ⚠️ **It's Mixolydian/blues, not weakened function** (§18 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| Blue notes are ♭3 and ♭5 | ⚠️ **They're inflections between the twelve notes** (§18 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| Non-Western music lacks harmony | ⚠️ **It has different developed systems; raga isn't a scale** (§19 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| Swing is a triplet feel | ⚠️ **Ratios vary with tempo and player** (§7 → `music-pitch-scales-rhythm-timbre-and-chords`) |
| Major = happy, minor = sad, universally | ⚠️ **Much more learned than it feels** (§21 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| Perfect pitch is required to be a musician | ⚠️ **Rare, largely early-training-linked, not predictive** (§3 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| 4'33" is a joke | ⚠️ **It's a claim about attention and framing** (§20 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| AI music is flooding what people listen to | ⚠️ **~50% of uploads, 1–3% of streams, 85% of those fraudulent** (§22.2) |
| The AI music lawsuits are settled | ⚠️ **Sony still litigating; fair-use ruling pending** (§22.1) |

---

## §24. Books

**Fundamentals**
| Author | Work | Why |
|---|---|---|
| **Laitz** | *The Complete Musician* | ⚠️ **The best single common-practice textbook** |
| **Aldwell & Schachter** | *Harmony and Voice Leading* | The standard, rigorous |
| **Fux** | *Gradus ad Parnassum* | ⚠️ **§13 → `music-functional-harmony-counterpoint-and-form`. 300 years old and still the best counterpoint pedagogy** |

**The physical and perceptual layer**
| **Sethares** | ***Tuning, Timbre, Spectrum, Scale*** | ⚠️ **The deep §3–§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning` book. Shows consonance depends on TIMBRE** |
| **Benson** | *Music: A Mathematical Offering* | ⚠️ **Free online. The maths of §2–§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning` done properly** |
| **Huron** | ***Sweet Anticipation*** | ⚠️ **§21 → `music-analysis-jazz-popular-non-western-and-meaning`. Expectation as the mechanism, empirically** |
| **Levitin** | *This Is Your Brain on Music* | Accessible psychoacoustics |

**Beyond common practice**
| **Levine** | ***The Jazz Theory Book*** | ⚠️ **§17 → `music-analysis-jazz-popular-non-western-and-meaning`. The standard** |
| **Everett** | *The Foundations of Rock* | ⚠️ **§18 → `music-analysis-jazz-popular-non-western-and-meaning` done seriously** |
| **Tagg** | *Everyday Tonality* | ⚠️ **Explicitly attacks classical theory's mis-fit with popular music** |
| **Nettl** | *The Study of Ethnomusicology* | §19 → `music-analysis-jazz-popular-non-western-and-meaning`'s methodology |
| **Cook** | *Music: A Very Short Introduction* | ⚠️ **Excellent on what the discipline even is** |

**⚠️ And the non-negotiable one**: **ear training.** ⚠️ **Theory without aural skills is
trivia.** **Interval and chord recognition, transcription by ear, and singing what you
read are what convert the symbols into hearing** — **and transcription in particular
teaches more per hour than any book here.**

---

## §25. Quick Reference

### 25.1 Picker
| Question | Where |
|---|---|
| Why do these notes sound good together? | ⚠️ **Harmonic series, simple ratios** (§2 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| Why does my tuner disagree with my ear? | ⚠️ **12-TET thirds are sharp** (§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning`) |
| Why does this progression feel like it's going somewhere? | ⚠️ **Functional harmony, leading tone, tritone** (§10 → `music-functional-harmony-counterpoint-and-form`) |
| Why does my part-writing sound thin? | ⚠️ **Check for parallel perfect intervals** (§10 → `music-functional-harmony-counterpoint-and-form`) |
| Why does this modal tune keep sounding like major? | ⚠️ **The tonic isn't established** (§6 → `music-pitch-scales-rhythm-timbre-and-chords`) |
| Why does my quantized track sound dead? | ⚠️ **Microtiming carries groove** (§7 → `music-pitch-scales-rhythm-timbre-and-chords`) |
| Why is my mix muddy in the low end? | ⚠️ **Close voicings inside critical bands** (§3 → `music-claims-harmonic-series-psychoacoustics-and-tuning`, §9 → `music-pitch-scales-rhythm-timbre-and-chords`) |
| How do I analyze a rock song? | ⚠️ **Modal + loop + timbral, not Roman numerals** (§18 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| How do I analyze late Romantic chromaticism? | ⚠️ **Neo-Riemannian** (§15 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| Why doesn't serialism catch on? | ⚠️ **It removes what statistical learning needs** (§20 → `music-analysis-jazz-popular-non-western-and-meaning`) |
| Can I sell an AI-generated track? | ⚠️ **Platform rights ≠ copyright; still unsettled** (§22.1) |
| Is AI taking over streaming? | ⚠️ **Uploads yes, listening no** (§22.2) |

### 25.2 Numbers
```
Octave                2:1     Perfect fifth   3:2     Perfect fourth  4:3
Major third           5:4     Minor third     6:5     Major triad     4:5:6
⚠️ Pythagorean comma   ~23.46 cents   ⚠️ Cents per octave  1200
⚠️ 12-TET fifth        ~2 cents flat  ⚠️ 12-TET major 3rd  ~14 cents SHARP
A440 standard         (⚠️ modern convention; historical pitch varied widely)
Human hearing         ~20 Hz – 20 kHz (⚠️ upper limit falls with age)
Spotify per stream    ⚠️ ~$0.003–0.005     Tidal  ~$0.012–0.015
⚠️ Streams for $100k at Spotify rates    ~20–33 million
⚠️ AI share of Deezer daily uploads      ~44% (Apr 2026), >50% (Jun 2026)
⚠️ AI share of Deezer STREAMS            1–3%, of which ~85% fraudulent
```

---

## §26. Method

**§1–§21 → `music-claims-harmonic-series-psychoacoustics-and-tuning`, `music-pitch-scales-rhythm-timbre-and-chords`, `music-functional-harmony-counterpoint-and-form`, `music-analysis-jazz-popular-non-western-and-meaning` rest on stable material** — **acoustics, psychoacoustics, tuning mathematics,
common-practice theory, jazz and popular practice, and ethnomusicological method** —
sourced from §24. ⚠️ **The tuning arithmetic in §4 → `music-claims-harmonic-series-psychoacoustics-and-tuning` is arithmetic and needed no
verification; the harmonic series in §2 → `music-claims-harmonic-series-psychoacoustics-and-tuning` is physics.**

**Two searches were run in August 2026**, on **AI music litigation and licensing** and
**streaming economics** — ⚠️ **the two areas that determine the conditions under which
music is actually made and paid for now, and where a 2024 answer would be badly wrong.**

**Confidence.** **High** in §2–§4 → `music-claims-harmonic-series-psychoacoustics-and-tuning`, which I'd defend most firmly and which is the part most
often taught wrong: ⚠️ **the comma is arithmetic, "well-tempered ≠ equal-tempered" is well
documented, and the point that key character was real and was abolished BY equal
temperament is a genuine and under-appreciated correction.**

**High** in §1 → `music-claims-harmonic-series-psychoacoustics-and-tuning`'s framing and §18 → `music-analysis-jazz-popular-non-western-and-meaning`'s argument. ⚠️ **The claim that classical theory
systematically mis-describes popular music — and that "pop is harmonically simple" is a
tool failure rather than a finding — is a position I hold and it's argued explicitly in
the literature (Tagg, Everett, Moore).** **I've flagged it as a position, not a fact.**

**High** in §22.1's chronology — **RIAA suits June 2024, UMG–Udio October 2025, Warner
settling with both in November 2025, Sony declining** — ⚠️ **which is consistent across
Reuters, Music Business Worldwide, Forbes and multiple legal trackers.** **The July 2026
summary-judgment hearing is reported by several sources**, ⚠️ **but at least one tracker
says schedules push a US fair-use ruling into 2027, and sources differ on which judge and
which combination of labels remain in which case — so treat the specific procedural
details as reported rather than confirmed.** **The AFM-suing-the-labels item and the GEMA
ruling I've flagged as reported and worth verifying independently.**

**High** in §22.2's Deezer figures, which come from Deezer's own newsroom and are
consistently reported. ⚠️ **The interpretive emphasis is mine and I'd defend it: the
upload/stream gap (roughly 44–50% of uploads versus 1–3% of streams, with ~85% of those
fraudulent) inverts the common alarm.** **This is a royalty-fraud and pool-dilution
problem, not evidence that listeners are switching to synthetic music.** ⚠️ **Note the
sourcing asymmetry I flagged in-text: Deezer is the only major platform publishing both
numbers, so the whole public picture rests on one company's disclosures — and the silence
of the others is itself worth noticing.**

⚠️ **Per-stream rates should be treated as rough bands.** **They are not posted rates;
they're back-calculated averages that vary substantially by listener geography, subscription
tier and distributor cut, and every source reports slightly different figures.**
