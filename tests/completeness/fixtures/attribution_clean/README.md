# Negative control for check_attribution — failure case 7

Clean authorship metadata, and a Python file that deliberately contains
`anthropic`, `Claude`, and `Generated with` **in its body**.

This tree must pass. If it does not, the checker has drifted back into scanning
contents, which DE-000l records as an unwinnable loop: the exclusion list grows
forever and the next legitimate mention trips it again. The word is topic. The
metadata is attribution.
