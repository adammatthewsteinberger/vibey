---
name: okta-workflows-branching
description: "Use when an Okta Workflows If/Else or If/ElseIf takes the wrong branch, or when designing branching / comparison logic in a flow: no implicit type coercion in comparisons ('6' Text vs 30 Number, '80' > '9' is false even though 80 > 9 is true) affecting True/False Compare, If/Else, If/ElseIf, Continue If, and Return Error If; the don't-nest-more-than-3-If/ElseIf guidance; passing a value directly into an If/ElseIf condition throwing an error (the Flow Control - Assign card tip-bug); Return / Continue If behaving as anonymous helper flows inside If/ElseIf and If Error blocks (proceeding after the block instead of halting); not being able to drag outputs from inside a branch to cards after the block (the Create Outputs / View Outputs feature); and If/Else supporting only ONE condition (And/Or/Not/XNOR). Triggers on wrong branch, silent wrong branch, True/False Compare, implicit datatype conversion, nested If/ElseIf, Continue If, Return Error If, drag outputs from a branch, Branching card outputs, one condition."
---

# Okta Workflows — If/Else and If/ElseIf Card Family (§1)

Six quirks in the branching/comparison card family. The #1 production bug in an Entra → Okta sync
is the silent wrong branch (1.1) caused by no implicit type coercion.

## Quirk 1.1 — No implicit type coercion in comparisons (silent wrong branch)

The True/False Compare, If/Else, If/ElseIf, Continue If, and Return Error If cards do NOT
auto-convert data types. Comparing value A `"6"` (Text) `<` value B `30` (Number) returns FALSE,
because when a number is passed as text a *text* (alphabetical) comparison is performed: `"80" > "9"`
is false even though `80 > 9` is true. This manifests constantly in Entra → Okta sync when
Graph/Okta API values arrive as strings.

- *Mechanism:* "Workflows does not perform implicit datatype conversions for comparisons" (Okta KB,
  "True/False Compare Card Output Result Might Be Incorrect," last updated Jan 9, 2026).
- *Workaround:* Explicitly set both value A and value B to the same type in the card's type
  dropdowns; when in doubt, coerce upstream with a Number or Text conversion card.
- *Source:* support.okta.com/help/s/article/true-false-compare-card-output-result-might-be-incorrect

## Quirk 1.2 — Nesting depth: don't exceed 3 nested If/ElseIf

Per AJ Ahrens, Workflows Team Lead at Okta (quoted verbatim in Max Katz "Workflows Tips #13,"
maxkatz.net, 2022/03/25): "Don't nest more than 3 If/Elseif statements. It is difficult to understand
how it works and debugging is even more challenging." This corroborates the user's finding that deep
nesting of branch/if-else cards is fragile.

- *Workaround:* Flatten to a single If/ElseIf with multiple conditions (evaluated top-down; only the
  *first* true branch runs), or precompute a boolean with True/False And/Or/Not/XNOR cards and feed
  it into one If/Else.
- *Source:* maxkatz.net Workflows Tips #13

## Quirk 1.3 — Passing a value directly into an If/ElseIf condition throws an error (tip-bug)

Per Max Katz Tips #13, quoting Okta staff: passing a value into an If/Elseif card produces an error.
Documented workaround at the time: "use Flow Control - Assign card inside the If/Elseif card to pass
in the value." Okta labeled this a "tip-bug" that "will be fixed."

- *Status:* Possibly resolved in a later release; treat as version-dependent and test in the target
  org.

## Quirk 1.4 — Return / Continue If behave differently inside If/ElseIf and If Error blocks

Inside an If/ElseIf or If Error block, these blocks behave as "anonymous helper flows." A Return (or
Continue If when false) does NOT halt the flow — it proceeds to the step immediately *after* the
If/ElseIf or If Error container. To actually halt, use Return Error, Return Error If, or a Continue If
placed *outside* the block.

- *Sources:* Okta docs branching_continueif.htm, flocontrol_return.htm, errorhandling_trycatch.htm

## Quirk 1.5 — Cannot drag outputs from inside a branch to cards after the block

"You can drag outputs from cards that run before the If/ElseIf into a condition or branch inside the
If/ElseIf, but you cannot drag outputs from inside a branch to cards that are run after the If/ElseIf.
This is because an output from inside a branch will be undefined any time a different branch is run."
Workaround: use the block's optional Outputs feature (View Outputs / Create Outputs) which assigns
values after whichever branch completes.

- *Sources:* Okta docs branching_branch.htm; support.okta.com
  how-to-use-if-else-if-elseif-and-if-error-card-outputs

## Quirk 1.6 — If/Else supports only ONE condition

The Branching - If/Else card doesn't support multiple conditions. Use True/False Compare cards
feeding an And/Or/Not/XNOR card, then pass the single boolean into If/Else; or use If/ElseIf.

- *Source:* maxkatz.net 2023/07/25
