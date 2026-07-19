# Planted violation for check_attribution

Three records, three distinct routes by which authorship leaks into a public
history: a `Co-Authored-By` trailer, a "Generated with" trailer, and an author
identity that is not the operator.

Note what is **absent**: any planted defect in a file body. Section 4.3 scopes
this checker to authorship metadata, and DE-000l records the unwinnable loop
that scanning contents produces. The clean fixture next door carries the word
"Claude" in a file on purpose, and must pass.
