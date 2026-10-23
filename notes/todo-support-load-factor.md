# TODO: support reaction factor differs between switchgear and cable bus

Status: input added (branch feat/cablebus-support-condition). Cable bus now has `support_condition`: `per_span` (1.0, default, unchanged results), `continuous` (1.1), `pinned`/`fixed` (0.5). Which one is right for a given run is still an engineering decision; the tested block rating governs.

| Module | Code | Support load under fault |
|---|---|---|
| Switchgear bus | `calculations/pecalc/switchgear.py` (`SPAN`, `support = force * L * k_r`) | R = k_r F L, with k_r = 1.1 for 3+ equal continuous spans (default `support_condition="continuous"`), 0.5 for a single pinned or fixed-fixed span |
| Cable bus | `calculations/pecalc/cablebus.py` (`support = fr.worst_n_per_m * inp.support_span_m / 4.44822`) | R = F L (factor 1.0), reported in lbf as "static; compare with tested block strength" |

F is the worst peak force per unit length (N/m) and L the support span (m).

For the same force and span, cable bus reports a support load about 9 % lower than the
switchgear module's continuous-beam reaction.

## Points to decide

- Is a cable bus run between blocks a continuous beam? Cables are flexible and are not
  moment-connected at the blocks, so R = F L (each block takes the load of one span)
  may be the right model. Busbars are rigid and continuous over supports, which gives
  the 1.1 F L interior reaction (3+ span beam tables) [from memory; check against IEEE 605
  and a beam-table reference].
- If cable bus keeps F L, state the reason in the module docstring. If it moves to 1.1 F L
  or a `support_condition` input, update the tests and the reported block check.
- Either way, the tested block rating (manufacturer short-circuit test per IEEE C37.23 /
  CSA C22.2 No. 273) is the governing comparison. The calculated load is only a screening
  value.
