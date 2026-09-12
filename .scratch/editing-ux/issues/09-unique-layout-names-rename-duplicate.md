# 09: Unique layout names, Rename, Duplicate

Spec: ../spec.md

**What to build:** Layout names are unique after normalisation (trim, strip characters illegal in filenames, compare case-insensitively). Creating a layout with a taken name gets " (2)", " (3)", and so on, never an overwrite; a blank name falls back to the template's suggested name. A Rename layout action opens a dialog prefilled with the current name and refuses a taken name inline (OK disabled, hint shown) rather than merging; renaming updates the remembered current layout. "Save as new layout" becomes Duplicate layout, defaulting to "<name> copy", auto-suffixing on collision, and switching to the copy. New layouts still inherit colors, position, and opacity from the current layout.

**Blocked by:** 08 (Layouts always have a file)

**Status:** ready-for-agent

- [ ] Creating "Azeron Cyborg II" twice yields files for "Azeron Cyborg II" and "Azeron Cyborg II (2)"; the first is untouched.
- [ ] "cyborg " and "Cyborg" are treated as the same name.
- [ ] Creating with a blank name uses the template's suggested name.
- [ ] Rename to a free name renames the file and the current layout pointer; rename to a taken name is refused inline and nothing changes on disk.
- [ ] Duplicate creates "<name> copy" (suffixed if taken), switches to it, and leaves the original unchanged.
- [ ] A new layout from a template keeps the current layout's colors, position, and opacity.
- [ ] Covered at the config-function seam and the settings-window seam.
