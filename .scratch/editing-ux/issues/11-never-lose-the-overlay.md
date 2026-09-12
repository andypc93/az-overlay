# 11: Never lose the overlay

Spec: ../spec.md

**What to build:** If the overlay's rectangle intersects no screen at all (after a resolution change, a typo in Precise position, or a stale saved position), it is moved to the nearest position where part of it is visible, on startup and whenever the layout is applied. Deliberate partial off-screen placement stays exactly where the user put it.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] A saved position entirely outside every screen is pulled back so at least a visible margin of the window is on the nearest screen, and the saved position is updated to the pulled-back one.
- [ ] A position half off the left, top, right, or bottom edge is left untouched.
- [ ] Applies on startup and on every apply (a Precise position edit to an off-screen value is corrected immediately).
- [ ] Covered at the overlay-widget seam with a controlled screen geometry.
