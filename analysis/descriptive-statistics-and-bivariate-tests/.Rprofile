# CRAN is pinned to a dated Posit Package Manager snapshot so that
# renv::install()/renv::restore() resolve the same package versions.
# With this snapshot and R 4.6.1, `quarto render` reproduces the committed
# rrmeasures-paper.tex byte for byte.
options(repos = c(CRAN = "https://packagemanager.posit.co/cran/2026-07-01"))
source("renv/activate.R")
