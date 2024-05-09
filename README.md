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
````

2. Navigate to cloned Repository:

```bash
cd Quisby
```

3. Install Required Deppendecies:

```bash
pip install -r requirements.txt
```


## Usage Instructions

Using Quisby involves two primary phases: Data Collection and Running the Application. Let's delve deeper into each phase:

### Data Collection

Ensure optimal performance and accurate visualization with Quisby by formatting and collecting your benchmark data appropriately. See detailed instructions [here](https://docs.google.com/document/d/1g3kzp3pSMN_JVGFrFBWTXOeKaWG0jmA9x0QMAp299NI).

### Running the Application

Before running Quisby, ensure that you have your data appropriately formatted, stored in a Google Spreadsheet, and that you've filled out the config.ini file with the required parameters. See detailed instructions [here](https://docs.google.com/document/d/1g3kzp3pSMN_JVGFrFBWTXOeKaWG0jmA9x0QMAp299NI).
For command line assistance, run:

```bash
python quisby.py --help
```


## Post-Execution Steps and Data Management

### Analyzing the Logs:

Dive into the quisby.log to get detailed information about the operations. This can be particularly helpful if you encounter any issues or want to understand the underlying processes better.

### Managing Spreadsheets:

The charts.json file serves as a repository for your spreadsheet names and IDs. Regularly back up this file to prevent any data loss. Additionally, this file can be used to quickly access or reference your spreadsheets without manually navigating through Google Sheets.

### Feedback and Troubleshooting:

If you encounter any issues or anomalies, first check the logs for any specific error messages. The log details combined with the structured data in charts.json will often provide clues to address the issue. If problems persist, consider reaching out to the application's support or development team.

These additions provide the user with a more holistic view of the application's operations and the data it generates. If there's anything else you'd like to add or modify, do let me know!

