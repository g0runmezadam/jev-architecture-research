# Curated Experiments

This directory contains the scripts and raw JSON outputs used by the archive's
main conclusions. Files are copied from the local Jev test harness so the public
research repository can be read without the private/model cache workspace.

## Reproduction order

1. Read the corresponding receipt in `../receipts/`.
2. Inspect the raw JSON before interpreting it.
3. Set the provider key in the environment only; never write it to a file.
4. Expect rate limits and endpoint limits, especially the 255-choice maximum.

The final pipeline script performs 720 calls and should not be run casually.
