# New layout creation and naming

Type: grilling
Status: resolved
Blocked by: 03

## Question

`_new_from_template` already writes the file immediately and later edits autosave,
so "new profile is auto-saved" holds in code. The remaining decisions are around
naming, since the name becomes the only identity once the unnamed state is gone:

1. **Name collision**: `save_profile` silently overwrites an existing file. Reject,
   auto-suffix ("Cyborg 2 (2)"), or ask?
2. **Rename**: needed? Today only copy (**Save as new layout…**) exists.
3. **Duplicate**: keep **Save as new layout…** under a new name (**Duplicate
   layout…**) or drop it?
4. **Default name** when the user leaves the name blank (today: device name).

Recommended: auto-suffix on collision; add Rename; keep Duplicate; default name =
template name.

## Comments

### Round 1 (2026-09-12, user confirmed every recommendation)

1a 2y 3a 4y 5a 6y 7keep. No round 2 needed.

## Answer

**Creation already autosaves.** New layout from template writes `profiles/<name>.json`
immediately and every later edit autosaves; combined with the invariant from
"Remove the unnamed layout state" this satisfies the original ask #4 with no new
behaviour.

**Names are unique** after normalisation: trim, strip `\/:*?"<>|`, compare
case-insensitively (what the Windows filesystem does anyway).

**Create with a taken name** auto-suffixes: "Azeron Cyborg II (2)", "(3)", ... Never
overwrites. Blank name falls back to the template's suggested name.

**Rename layout…** added to the More menu; dialog prefilled with the current name.
Renaming onto a taken name is rejected inline (OK disabled, hint shown), never
suffixed or merged. Rename updates the current-layout pointer in config.json.

**Duplicate layout…** replaces "Save as new layout…". Default name "<name> copy";
collision auto-suffixes; switches to the copy as today.

**Inheritance.** A new layout keeps the current layout's colors, position, and
opacity; only pads, sticks, and dimensions come from the template (unchanged).
