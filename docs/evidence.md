# Evidence and validation

## Coursework provenance

The source material is the University of Edinburgh MSc Threaded Programming
assessment 2 submission, 2024–25. The compiler and thread-count timing
entries in the submitted report (§2.1 and §2.2, pages 4–5) match the 36
entries in the four submitted timing files. The course targeted Cirrus with
GNU 10.2 and Intel 20.4 at `-O3`. The submitted build configuration and
benchmark script name those toolchains.

Comparison with the supplied `CW2.tar` identified the integrand module
and header as unchanged starter files. The recursive and queue solver
sources and build file differ from their supplied counterparts. The
coursework snapshot is a mix of supplied code and submitted modifications.
This portfolio repository contains a new write-up, curated measurements
and independent analysis and plotting. The starter, assessment, source,
and full submission remain in the local archive.

## Historical evidence

`data/cirrus-timings.csv` retains the four complete reported timing series.
The historical benchmark script requested 1, 2, 4, 6, 8, 12, 16, 24 and
32 threads and collected one sample per configuration. The available
table records timings rather than the integral from every run. Exact
builds, host metadata, affinity, actual team sizes and independent repeats
are unavailable.

The report labels the second timing series as shared queue. The submitted
report also describes thread-private queues with work stealing, which
the saved queue source scaffolds. The saved code dequeues work but omits
its processing and never updates the integral. A fresh one-thread run of
that exact saved source printed zero. The seconds in the only surviving
temporary output match the final GNU queue row at 1.311370 s, but a
matching duration does not identify the executable. That output's
unattributed estimate, `-0.6877178`, differs from the analytic reference.
The queue curves have unresolved implementation provenance.

## Independent numerical reference

The integrand calls a first-order Euler update with a constant forcing
amplitude at each evaluation point and zero initial state. In real
arithmetic, after $k$ updates with step $h$ the fraction of the forcing
amplitude reached is $1-(1-h)^k$. The update count remains constant on
each of 2,000 equal-width subintervals of the integration domain. The
forcing term is sinusoidal, so each term can be integrated with its
antiderivative and scaled by the corresponding recurrence factor.

The reference was calculated three ways.

1. Sum the exact piecewise antiderivative differences at 70 decimal
   digits.
2. Sum the unweighted and recurrence-weighted cosine boundary terms as
   two complex geometric series, using 70 decimal digits.
3. Evaluate the same piecewise integrals with a half-angle identity,
   `expm1` for the recurrence factor and `math.fsum` for stable
   double-precision summation.

The high-precision methods agree within $10^{-60}$. The double-precision
sum differs by less than $10^{-14}$. The first high-precision digits are
`-0.169820118267307940760558205132`. This integrates the ideal real
recurrence. The compiled workload uses finite-precision arithmetic and
the original program prints the integral to seven significant digits.

The recursive solver's printed estimate `-0.1699471` differs by
approximately `1.27e-4`. This exceeds the nominal local tolerance
`1e-6`. Every child inherits the full parent tolerance, and the coarse
and refined estimates can agree without providing a reliable global
bound. The source review did not isolate the cause of the observed
numerical discrepancy.

## Fresh local experiment

`data/local-comparison.json` records the environment, compile flags,
each raw timing and rounded result, sample order, and medians. The
rebuild compiled the saved C sources without edits with Apple Clang,
`-O3`, and the installed x86-64 LLVM OpenMP runtime. The executables
ran under Rosetta on an Apple M1. A separate OpenMP probe confirmed team
sizes of one and four with the respective environment settings. Actual
team size was not instrumented inside the unmodified solver.

Each measured sample started a fresh process. Three pairs alternated
the order of one and four requested threads. The original program's
timer includes endpoint evaluations and the entire OpenMP parallel
region. This measures the saved executable on one input and one local
environment. It neither reproduces the Cirrus environment nor isolates
task scheduling from the rest of the program. The observed numerical
difference applies to the measured input and these builds.

The measurement script is retained locally. Archive and compilation input
hashes are recorded in `data/archive-check.json`. The curated data and
plotting command reproduce the chart without access to the University
starter files.
