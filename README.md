# Awsdsc (abbreviation of AWS describe)

Universal describe command for AWS resources (this is an **EXPERIMENTAL** project).

## Installation

```
pip install awsdsc
```

## Demo

![demo](demo.gif)

## Basic Usage

Firstly setup AWS credentials (usually by running `aws configure`) before using.

Then run the following command.

```
awsdsc [--profile ${YOUR_PROFILE_NAME}]
```

You will be prompted to input type and query for AWS resources to describe.

For more details, please run `awsdsc --help` and check the help text.
