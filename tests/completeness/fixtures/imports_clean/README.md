# Negative control for check_import_graph

The same two rules as the planted tree, over a tree that obeys them.

`lab.ledger.chain` constructs `TrialResult`, which is exactly what the
`constructed_only_in: ["lab.ledger.*"]` rule permits. That construction is the
point of the control: a checker that flagged it too would still reject the
planted tree, and `test_import_graph_rejects_violation` would still pass — while
the rule had in fact become a blanket ban on the symbol it was written to
protect.
