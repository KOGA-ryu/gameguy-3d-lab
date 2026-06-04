# Gothic Railing Post Research Findings V0

## Scope

This note is for Gothic-inspired railing posts and newels. It is morphology
research for game-asset generation. It does not claim strict historical
accuracy, structural safety, fabrication readiness, or building-code
compliance.

## Source Links

- [Encyclopaedia Britannica: Gothic Architecture](https://www.britannica.com/art/Gothic-architecture)
- [RIBA: Gothic Architecture](https://www.architecture.com/knowledge-and-resources/knowledge-landing-page/gothic-gothic-revival-neo-gothic)
- [Encyclopaedia Britannica: Foil](https://www.britannica.com/technology/foil-architecture)
- [The National Gallery: Quatrefoils](https://www.nationalgallery.org.uk/paintings/glossary/quatrefoils)
- [Encyclopaedia Britannica: Newel](https://www.britannica.com/technology/newel)

User-supplied references also guide this lane: compound pier diagrams, Gothic
railing/panel references, and sacred-geometry pattern fields.

## Useful Terms

`newel_post`

The larger post at a stair foot, landing, turn, or railing termination. In this
repo it is the best first railing post target because it can carry plinth,
shaft, cap, finial, rail sockets, and face ornament.

`balustrade`

The whole railing assembly: posts or newels, handrail, base rail, balusters,
panels, infill, sockets, and ornament.

`plinth`

The bottom block or base mass that makes the post feel grounded.

`shaft`

The main vertical body. It can be square, round, tapered, fluted, clustered, or
compound.

`collar`

A ring, band, necking, or clamp-like transition around the shaft.

`cap`

The upper block or moulded closure above the shaft.

`finial`

The top ornament, often a ball, spire, pyramid, knob, or pinnacle-like form.

`pinnacle`

A small vertical spire-like termination. For this repo it becomes a finial
style, not a structural claim.

`tracery`

Patterned linework associated with Gothic openings and screens. In the repo it
means selected 2D linework or profiles promoted into raised trim, ribs, cuts,
or infill.

`foil`

Lobed ornament vocabulary such as trefoil, quatrefoil, and cinquefoil. These
are useful because they can be generated from circles, radial repeats, and
selected offsets.

`blind_tracery`

Tracery applied to a closed surface instead of an open window. This is the best
first post-face ornament because it avoids fragile through-holes.

`crocket`

Small repeated projections along an edge, cap, or finial. In this repo they
should start as low-poly triangular or capsule protrusions with array controls.

## Research Translation

The Gothic look is not one object. It is a stack of repeatable geometric moves:

- pointed arch profiles on faces and panels
- clustered or compound shafts
- square-to-octagon-to-round transitions
- collars, beads, torus rings, coves, and fillets
- trefoil/quatrefoil/rosette motifs from radial circles
- vertical emphasis through slender shafts and finials
- selective line promotion from dense construction geometry
- shallow relief before deep cuts

For railing posts, the first useful styles are:

- buttress newel
- clustered shaft newel
- blind tracery box newel
- pinnacle newel
- crocketed finial newel

Each style can be made from simple geometry if its parts are named and the
ledger owns the detail decisions.

## Design Rule

Do not bake the style into Blender. Put it in the style sheet:

```text
taxonomy name -> source shapes -> operations -> tool sequence
```

Then later compilers can produce deterministic JSON and Blender can preview or
export the result.
