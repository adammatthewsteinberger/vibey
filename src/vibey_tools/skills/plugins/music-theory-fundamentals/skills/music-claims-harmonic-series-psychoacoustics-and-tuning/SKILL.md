---
name: music-claims-harmonic-series-psychoacoustics-and-tuning
description: "Use when asking why music theory says what it says: the three layers — acoustic fact, perceptual finding and stylistic convention — and why conflating them makes theory sound arbitrary, the harmonic series and what it does and does not explain, psychoacoustics including consonance, critical bands and pitch perception, and tuning and temperament from just intonation through equal temperament and what each compromise costs. Includes the router for the whole music-theory-fundamentals reference."
---

# Music Theory Fundamentals: Three Kinds of Claim, the Harmonic Series, Psychoacoustics, and Tuning

> **Part 1 of 5** of the *Music Theory Fundamentals* reference (plugin `music-theory-fundamentals`), covering §0–§4. Sibling skills: `music-pitch-scales-rhythm-timbre-and-chords` (§5–§9), `music-functional-harmony-counterpoint-and-form` (§10–§14), `music-analysis-jazz-popular-non-western-and-meaning` (§15–§21), `music-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The theory is centuries stable. Two areas are live. See §22 → `music-reference` for AI music licensing and litigation, and streaming economics.

> **⚠️ Read §1 first.** **"Music theory" names three different things stacked on top of
> each other**, **and the discipline's biggest failure mode is presenting the third as
> though it were the first.**
>
> **⚠️ GOTCHA** boxes mark things taught confidently that are either false, or true only
> of one repertoire.
>
> **The three ideas that organize this document:**
> 1. **⚠️ There is a real physical substrate — the harmonic series — and it genuinely
>    constrains what sounds consonant** (§2–§3). **This is more than art theory has, and
>    it is far less than "music theory is physics."**
> 2. **⚠️ What is taught as "music theory" is overwhelmingly the grammar of European
>    common-practice tonality, roughly 1650–1900.** **It's a superb description of a
>    specific repertoire.** ⚠️ **It systematically mis-describes jazz, most popular music,
>    and nearly all non-Western music** (§17–§19 → `music-analysis-jazz-popular-non-western-and-meaning`).
> 3. **⚠️ Theory is descriptive, not prescriptive — it was reverse-engineered from music
>    that already existed.** **"You can't use parallel fifths" means "Bach didn't, in this
>    genre, for these reasons."** **Debussy used them constantly.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ What kind of claim is this? — READ FIRST** | **§1** |
| **The harmonic series** | **§2** |
| Psychoacoustics | §3 |
| **⚠️ Tuning and temperament** | **§4** |
| Pitch, intervals, notation | §5 → `music-pitch-scales-rhythm-timbre-and-chords` |
| Scales and modes | §6 → `music-pitch-scales-rhythm-timbre-and-chords` |
| **Rhythm and meter** | **§7 → `music-pitch-scales-rhythm-timbre-and-chords`** |
| Timbre | §8 → `music-pitch-scales-rhythm-timbre-and-chords` |
| Chords | §9 → `music-pitch-scales-rhythm-timbre-and-chords` |
| **Functional harmony and voice leading** | **§10 → `music-functional-harmony-counterpoint-and-form`** |
| Cadence and phrase | §11 → `music-functional-harmony-counterpoint-and-form` |
| Modulation and chromaticism | §12 → `music-functional-harmony-counterpoint-and-form` |
| Counterpoint | §13 → `music-functional-harmony-counterpoint-and-form` |
| Form | §14 → `music-functional-harmony-counterpoint-and-form` |
| Analytical methods | §15 → `music-analysis-jazz-popular-non-western-and-meaning` |
| Melody | §16 → `music-analysis-jazz-popular-non-western-and-meaning` |
| **Jazz harmony** | **§17 → `music-analysis-jazz-popular-non-western-and-meaning`** |
| **Popular music — and why classical theory fails it** | **§18 → `music-analysis-jazz-popular-non-western-and-meaning`** |
| **Non-Western systems** | **§19 → `music-analysis-jazz-popular-non-western-and-meaning`** |
| 20th–21st century | §20 → `music-analysis-jazz-popular-non-western-and-meaning` |
| Music and meaning | §21 → `music-analysis-jazz-popular-non-western-and-meaning` |
| **What's live** | **§22 → `music-reference`** |
| Misconceptions | §23 → `music-reference` |
| Books | §24 → `music-reference` |
| Quick reference | §25 → `music-reference` |

---

## §1. ⚠️ Three Layers, Three Kinds of Claim

```
1. ACOUSTICS — ⚠️ physics. Measurable, universal, not up for debate
   Frequency ratios, the harmonic series, beating, resonance (§2, §4)

2. PSYCHOACOUSTICS — ⚠️ how HUMAN hearing works. Empirical, largely
   cross-cultural, with real variation at the edges
   Critical bands, roughness, octave equivalence, pitch perception (§3)

3. ⚠️ STYLISTIC GRAMMAR — one culture's practice, codified
   Functional harmony, voice-leading rules, forms, "avoid" notes. ⚠️ This is
   what "music theory" usually means, and it is NOT universal (§10–§14)
```

> **⚠️ GOTCHA — the octave is close to a genuine human universal; almost nothing else in
> layer 3 is.** ⚠️ **Octave equivalence (notes an octave apart are heard as "the same
> note") appears in essentially every documented musical culture and has a clean physical
> basis: a 2:1 frequency ratio, and every harmonic of the upper note is already a
> harmonic of the lower.** **The perfect fifth (3:2) is nearly as widespread.**
> **⚠️ Beyond that, scale structures, harmonic practice, rhythmic organization and
> consonance judgements vary enormously**, **and the confident claim that Western tonality
> reflects natural law is doing a lot of unearned work with a small number of real
> acoustic facts.**

**⚠️ The practical consequence for a learner**: **learn common-practice theory — it's a
coherent, powerful, well-documented system and it's the shared vocabulary.** ⚠️ **Just
hold it as "the grammar of a specific repertoire," not "how music works."** **You will
otherwise spend years confused about why the music you actually listen to keeps breaking
the rules.**

---

# PART I — THE PHYSICAL SUBSTRATE

---

## §2. The Harmonic Series

**⚠️ Almost everything in Western harmony is downstream of one physical fact: a vibrating
string or air column vibrates at a fundamental frequency AND at whole-number multiples of
it simultaneously.**

```
Harmonic:  1     2     3     4     5     6     7     8    ...
Ratio:     1:1   2:1   3:2   4:3   5:4   6:5   7:6   8:7
Interval:  fund. 8ve   5th   4th   M3    m3    ⚠️ ~m3♭  M2
On C:      C     C     G     C     E     G     ⚠️B♭(flat) C
```
**⚠️ Why this matters:**
- **⚠️ The intervals we call consonant are the SIMPLE ratios, and they appear early in the
  series.** **This is not arbitrary.**
- **⚠️ The major triad (4:5:6) is literally harmonics 4, 5 and 6.** **It's sitting inside
  every note you play.**
- **⚠️ The MINOR triad is NOT in the series in the same way**, ⚠️ **which is a genuine
  asymmetry that theorists have been arguing about for centuries** — **attempts to derive
  it from an "undertone series" have no acoustic basis and are best treated as
  historically interesting rather than correct.**
- **⚠️ The 7th harmonic is noticeably flat of any note on a piano.** **It's the sound in
  barbershop sevenths and blues intonation, and equal temperament cannot produce it.**
- **Timbre is largely the relative amplitude of the harmonics** (§8 → `music-pitch-scales-rhythm-timbre-and-chords`).

**⚠️ The crucial caveat**: **the harmonic series explains why some intervals are
acoustically privileged.** ⚠️ **It does NOT explain why 18th-century Europe built
functional harmony out of them, any more than the physics of pigment explains
Impressionism.** **Physics constrains; culture chooses within the constraint.**

---

## §3. Psychoacoustics

**Pitch** ≈ **perceived frequency, logarithmically** — ⚠️ **which is why an octave is a
DOUBLING, and why musical intervals are ratios rather than differences.**
**⚠️ Critical bands and roughness — the best current account of dissonance**: **two tones
close in frequency but not identical fall within the same critical band on the basilar
membrane and produce beating, heard as ROUGHNESS.** ⚠️ **Simple-ratio intervals have
harmonics that either coincide exactly or stay well separated; complex ratios produce many
near-coincidences and therefore beating.** **This gives sensory dissonance a real
mechanistic basis (Helmholtz, Plomp & Levelt).**
> **⚠️ GOTCHA — sensory dissonance and musical dissonance are different things and
> conflating them causes endless confusion.** ⚠️ **Sensory roughness is largely universal
> and measurable.** **Which intervals count as musically dissonant — requiring resolution,
> sounding unstable — is LEARNED and historically variable.** **The tritone was the
> *diabolus in musica*; it's the ordinary sound of a dominant seventh and the default
> jazz vocabulary.** ⚠️ **The perfect fourth is consonant melodically and was treated as a
> dissonance requiring resolution in counterpoint. Nothing physical changed.**

**Other robust findings**: **the missing fundamental** (⚠️ **you hear a pitch that isn't
physically present, from its harmonics — which is why small speakers can suggest bass**);
**masking**; **the auditory scene analysis that lets you follow one line in a texture
(Bregman)**; **and equal-loudness contours (Fletcher-Munson) — ⚠️ hearing sensitivity
varies with frequency AND with level, which is why mixes translate badly across
volumes.**
**⚠️ Absolute pitch is rare, partly genetic, strongly associated with early musical
training, and notably more common among speakers of tone languages** — **and it is not
required for, or especially predictive of, musicianship.**

---

## §4. Tuning and Temperament

**⚠️ Here is the fundamental problem of Western tuning, and it is unfixable arithmetic:**

```
⚠️ Stack 12 perfect fifths (3:2):   (3/2)^12  = 129.746...
⚠️ Stack 7 octaves (2:1):           2^7       = 128
⚠️ They do not meet. The gap is the PYTHAGOREAN COMMA (~23.46 cents)
```
> **⚠️ GOTCHA — you cannot have pure octaves, pure fifths, AND pure thirds in a
> twelve-note system.** ⚠️ **This is not an engineering limitation to be solved; it is
> arithmetic.** **Powers of 3 are never powers of 2.** **Every tuning system in history is
> a decision about WHERE to put the error.**

```
PYTHAGOREAN   ⚠️ pure fifths, badly out-of-tune thirds. Fine for medieval
              parallel organum; unusable for triadic harmony
JUST INTONATION  ⚠️ pure simple ratios in ONE key. Beautiful there, unusable
              elsewhere — and it can't modulate. Barbershop and some a cappella
              groups approximate it by ear in real time
MEANTONE      ⚠️ narrows fifths to purify thirds. Excellent in near keys;
              produces the notorious "wolf fifth" in remote ones
WELL TEMPERAMENTS  ⚠️ all keys usable, each with a DIFFERENT CHARACTER.
              This is the world Bach's Well-Tempered Clavier belongs to
EQUAL (12-TET) ⚠️ the error spread perfectly evenly. Every fifth 2 cents flat
              (unnoticeable); ⚠️ every major third ~14 cents SHARP (audible)
```
**⚠️ Two corrections worth having:**
- **⚠️ "Well-tempered" does not mean "equal-tempered."** **Bach's title almost certainly
  refers to a well temperament in which all keys are usable but each retains distinct
  colour — which is the entire artistic point of a cycle through all 24 keys.** **Equal
  temperament makes all keys identical, which would make the project far less
  interesting.**
- **⚠️ Key characteristics were real, and equal temperament abolished them.** **When
  Baroque and Classical writers describe D minor as grave or E major as radiant, they
  were describing genuine acoustic differences produced by unequal temperament.**
  ⚠️ **Under 12-TET, key character is a matter of instrument register and open strings,
  not tuning — the claim survives as folklore after its cause was removed.**

**⚠️ What 12-TET bought**: **unrestricted modulation, transposition, and fixed-pitch
instruments that work in every key.** ⚠️ **What it cost**: **every major third is
noticeably sharp, and pure intervals are unavailable.** **Singers, string players and
trombonists adjust away from it constantly by ear — which is why unaccompanied choirs
sound different from pianos, and why they sometimes drift.**
**⚠️ Cents**: **1200 per octave, 100 per equal-tempered semitone.** **The standard unit for
all of this.**

---

# PART II — MATERIALS
