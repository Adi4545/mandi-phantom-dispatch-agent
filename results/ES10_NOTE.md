# ES10 note

`cvar_10_inr` and any "worst-10%" figure in the historical experiment CSVs (`exp1` through `exp17`) is the mean of observations at or below a sample 10% quantile. That is not ES10.

ES10, as used in `paper/manuscript.md` and `revision/results/`, is the mean of an exact worst-10% mass with a fractional weight on the boundary observation. See `revision/es10.py`.
