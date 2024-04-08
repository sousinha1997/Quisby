# Quisby

## Overview

Quisby is an advanced data preprocessing and visualization tool designed to transform benchmark regression data into comprehensible formats within Google Spreadsheets. It simplifies the intricate process of benchmark data analysis by offering intuitive functionalities, allowing users to obtain actionable insights more effortlessly.

## Target Audience

Quisby is tailored for individuals, data scientists, researchers, and professionals who seek to plot and analyze benchmark results.

## Main Features

### Benchmark Data Plotting

Quisby supports a variety of popular benchmarks including but not limited to:
- linpack
- streams
- specjbb
- speccpu
- fio
- uperf
- coremark
- coremark_pro
- passmark
- pypref
- phoronix
- etcd
- auto_hpl
- hammerdb
- aim
- pig
- reboot

### Spreadsheet Comparison

Users have the capability to compare two benchmark data spreadsheets, facilitating a holistic analysis.

## Prerequisites

### Software

- Python version 3.9 or above.

### Google Service Account

To utilize Google Sheets API, you need to set up a Google Service Account. Follow the steps mentioned [here](https://docs.google.com/document/d/19M2sG6BZXch7F91oYmAKtMlgrhjc0Z749PmF8YeugVE/edit).

### Other Requirements

- Install additional dependencies from the `requirements.txt` file provided in the Quisby repository.
- Create a `config.ini` file with the specified content.

## Installation Process

1. Clone the Quisby Repository:

```bash
git clone https://github.com/sousinha1997/Quisby.git
