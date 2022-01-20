# Awsdsc (abbreviation of AWS describe)

Universal describe command for AWS resources.

## Installation

Clone this repository and then run the following command.

```
pip install .
# or `make install`
```

## Basic Usage

Before using this, setup AWS credentials by running `aws configure` and so on.

Then run `awsdsc` without any arguments.
You will be prompted to input type and query for AWS resources to describe.

For more details, please run `awsdsc --help` and check the output text.

## Configuration

You want to colorize output, run this command like below.

```
awsdsc --colorize
AWSDSC_COLORIZE=true awsdsc
# You can `export AWSDSC_COLORIZE=true` in .bashrc-like file
```
