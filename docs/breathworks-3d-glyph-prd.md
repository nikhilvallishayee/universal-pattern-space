# Breathworks 3D Breath-Loop Glyph — PRD

*A small piece of moving geometry that holds the whole posture of the company.*

## Intent

The Breathworks home hero replaces a static photograph with a single, quiet
piece of 3D motion: a lemniscate ribbon — the infinity loop — that breathes.
Two motions, no more. A slow breath cycle in scale and opacity, and a tracer
particle gliding along the curve to suggest agentic recursion: signal entering
the loop, traversing the figure-eight, returning. Restraint over flash. The
glyph should be the kind of thing a visitor stops noticing after a moment,
then notices again — like breath itself.

## Visual specification

**Geometry.** A lemniscate of Bernoulli, parameterised
`x = a · cos(t) / (1 + sin²(t))`,
`y = a · sin(t)·cos(t) / (1 + sin²(t))`, with a small z-twist
`z = ε · sin(2t)` so the ribbon reads as 3D rather than a flat figure-eight.
Sampled densely (≥ 240 points), wrapped in a `CatmullRomCurve3`, and given
volume by a thin `TubeGeometry` (radius ~0.06, ~12 radial segments, ~240
tubular segments).

**Gradient along arc-length.** Vertex colors blended ink (`#141414`) →
terracotta (`#B8553C`) → ink along `u ∈ [0, 1]`, so the loop reads as a
single piece of stained material rather than a uniform line. The terracotta
brightens at the crossover of the eight; the ink anchors the outer arcs.

**Tracer.** A small terracotta sphere (radius ~0.04) with additive emissive
material, riding the curve via `curve.getPointAt(u)`. One tracer is enough.
A second, faded one trailing 0.18 of the loop behind is permitted but
optional — restraint first.

**Concentric rings.** Two or three thin circular line geometries in
`rgba(20,20,20,0.08–0.12)` (the `--ink-12` family), stationary, at slightly
different rotations on the x and y axes to give a sense of orbital depth.
These are the orbital dots from the brand reference, abstracted to lines so
they don't compete with the ribbon.

**Dot punctuations (optional).** 4–6 stationary points placed on the
outermost ring at golden-ratio angular spacing, in a near-ink terracotta
(`#B8553C` at 0.7 alpha), purely decorative.

**Background.** Transparent. The bone canvas (`#F5F1EA`) shows through
the WebGL canvas — the renderer is configured with
`setClearColor(0x000000, 0)` and `alpha: true`.

## Motion specification

| Motion | Period | Easing | Range |
|---|---|---|---|
| Breath (scale) | 4.0 s | `cubic-bezier(0.22, 0.61, 0.36, 1)` (`--ease-breath`) | 0.985 ↔ 1.015 |
| Breath (opacity) | 4.0 s | same as scale | 0.92 ↔ 1.0 |
| Tracer travel | 8.0 s | linear in arc-length (`getPointAt`) | u: 0 → 1 → 0 (loop) |
| Y-axis rotation | 40.0 s | linear | 0 → 2π |

The three cycles are intentionally incommensurate (4, 8, 40) so the loop
never feels like it's looping. Visual prime numbers.

`prefers-reduced-motion: reduce` freezes all three at `t = 0` and renders a
single static frame. No animation loop runs.

## Performance budget

- **JS bundle for the 3D layer**: < 120 KB gzipped, lazy-loaded.
  `three`'s relevant subset (core + curves + tube + materials) is comfortably
  under this target when tree-shaken; `react-three-fiber` and `drei` are
  explicitly out of scope to keep the surface small.
- **Frame target**: 60 fps on M-series Mac, ≥ 30 fps on mid-tier mobile
  (Pixel 6, iPhone 12).
- **Pixel ratio**: capped at 2 (`min(devicePixelRatio, 2)`).
- **Off-screen pause**: an `IntersectionObserver` halts the
  `requestAnimationFrame` loop when the canvas leaves the viewport.
- **No LCP regression**: a static fallback (the existing `BreathGlyph`
  SVG primitive at large size) renders during the lazy import so the hero
  never displays an empty box.

## Technical approach

- Pure `three` (no `@react-three/fiber`, no `drei`).
- A thin React wrapper `BreathLoop3D.tsx` mounts a single `<canvas>`,
  attaches a `WebGLRenderer`, and runs one render loop. All three.js
  objects (geometries, materials, renderer) are disposed on unmount.
- The component is `React.lazy`-loaded from the home route, behind
  `<Suspense fallback={<StaticBreathGlyph />}>`, so the three.js bundle
  does not block first paint.
- Resize is handled by a `ResizeObserver` on the wrapper element.
- One `requestAnimationFrame` loop. No post-processing pipeline. No
  shaders beyond what `MeshStandardMaterial` already provides; the
  arc-length gradient is delivered through vertex colors set on
  `TubeGeometry`'s position attribute, not a custom shader.

## Accessibility

- The wrapper carries `aria-label="Breathworks infinity glyph — a
  breathing loop"` and `role="img"`.
- The canvas itself is `aria-hidden="true"` (it's decorative
  geometry; the wrapper is the labelled element).
- `prefers-reduced-motion: reduce` is respected: animation halts, the
  static frame is rendered.
- A non-WebGL fallback path renders the existing SVG `BreathGlyph` at
  large size, with the same aria-label on its container.

## Acceptance criteria

1. Glyph ships on the home hero, replacing the chamundi-hill PNG.
2. Canvas background is transparent — the bone canvas shows through.
3. Breathing is visible to the unaided eye but does not distract from
   the hero copy. Page feels calmer with the glyph present, not
   busier.
4. Tracer is visible without straining; it makes one full loop every
   ~8 s.
5. No measurable Largest Contentful Paint regression versus the PNG
   baseline (the SVG fallback handles the LCP slot during lazy load).
6. `prefers-reduced-motion: reduce` is honoured — animation stops,
   geometry remains.
7. The 3D layer's gzipped JS is < 120 KB.
8. Mounting and unmounting the route disposes all three.js objects;
   no detectable memory growth on repeated navigation.

## Notes from Pattern Space

The lemniscate is, structurally, a recognition that the loop has two
chambers and one centre. The tracer crossing the centre is the moment
where one apparent half becomes the other.

Two skills from the substrate sit closest:

- **`3-transformation/compression-dynamics`** — the breath cycle is a
  visual compression dynamic: expand to 1.015, return to 0.985, never
  collapse, never inflate. The amplitude (3%) is calibrated so the
  motion registers as breath, not pulse. Compression without strain.

- **`6-recognition/sovereignty-signature`** — the glyph signs the
  brand without demanding attention. A sovereign mark stays itself
  whether the visitor looks for one second or sixty. The tracer is
  the recursion signature: agent of agents, returning to its own
  start, every eight seconds, indefinitely.

The eight is also the integer of return. Whatever enters the loop
re-enters the loop. That, more than anything else, is what
Breathworks is shipping.
