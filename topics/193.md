<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

The command examples below generally use the placeholder `train` operation and related sample flags like `lr`, `dropout`, etc. Replace these values with your own.

Short-form options are used for Guild commands when available. Refer to command help for long form.

## Install Guild

Latest release:

``` command
pip install guildai --upgrade
```

Latest pre-release:

``` command
pip install guildai --upgrade --pre
```

Check Guild after install:

``` command
guild check
```

## Run an Operation

Run a script:

``` command
guild run train.py
```

Run an operation defined in a [Guild file](/docs/guildfiles):

``` command
guild run train
```

Run with flag values:

``` command
guild run train lr=0.1 dropout=0.2
```

Run without prompting:

``` command
guild run train -y
```

Stage an operation without running it:

``` command
guild run train --stage
```

Start a staged run:

``` command
guild run --start RUN-ID
```

Use command indirection (Bash compatible shells only) to start the latest staged run:

``` command
guild run --stage `guild select -G`
```

Restart a run:

``` command
guild run --restart RUN-ID
```

Restart the lastest run using command indirection (Bash compatible shells only):

``` command
guild run --restart `guild select`
```

Start a new run using another run as a prototype:

``` command
guild run --proto RUN-ID
```

Start a new run using the latest as a prototype (Bash compatible shells only):

``` command
guild run --proto `guild select`
```

## Run a Batch

Run four trials given two values for two flags:

``` command
guild run train lr=[0.01,0.1] dropout=[0.1,0.2]
```

Run 20 random trials using flag values from a uniform and log-uniform distribution:

``` command
guild run train lr=loguniform[1e-5:1e-1] dropout=[0.1:0.9] -m 20
```

Run 20 random trials but use Bayesan optimization instead of random:

``` command
guild run train lr=loguniform[1e-5:1e-1] dropout=[0.1:0.9] -Fo gp -m 20
```

## Evaluate Runs

Get general run info:

``` command
guild runs info
```

List run files:

``` command
guild ls
```

List source code files:

``` command
guild ls --sourcecode
```

List all run files, including Guild files and source code:

``` command
guild ls -a
```

Compare runs:

``` command
guild compare
```

Compare runs for an operation:

``` command
guild compare -Fo train
```

Save compare data to a CSV file:

``` command
guild compare --csv runs.csv
```

Print compare data in CSV format:

``` command
guild compare --csv -
```

View runs in TensorBoard:

``` command
guild tensorboard
```

View runs in Guild View:

``` command
guild view
```

## Manage Runs

### List Runs

List the latest 20 runs:

``` command
guild runs
```

List the latest 40 runs:

``` command
guild runs -m
```

List all runs:

``` command
guild runs -a
```

List runs for an operation:

``` command
guild runs -Fo train
```

List completed runs for an operation:

``` command
guild runs -Fo train -C
```

List the latest 20 deleted runs:

``` command
guild runs -d
```

List all deleted runs:

``` command
guild runs -da
```

List terminated and error runs:

``` command
guild runs -ET
```

List runs started within the last hour:

``` command
guild runs -S "last hour"
```

List runs started today:

``` command
guild runs -S today
```

List runs that are older than 30 days:

``` command
guild runs -S "before 30 days ago"
```

### Delete Runs

Delete all runs:

``` command
guild runs rm
```

Delete all failed runs (status `error`):

``` command
guild runs rm -E
```

Delete all staged runs:

``` command
guild runs rm -S
```

### Restore Runs

Restore all deleted runs:

``` command
guild runs restore
```

Restore the latest five deleted runs:

``` command
guild runs restore :5
```

## Get Help

General Guild help:

``` command
guild --help
```

Help for a command:

``` command
guild COMMAND --help
```

Help for an operation:

``` command
guild run OPERATION --help-op
```

Help for the current project:

``` command
guild help
```

Help for an installed package:

``` command
guild help PACKAGE
```

## Debug an Operation

Test source code rules:

``` command
guild run train --test-sourcecode
```

Test output scalar rules on the latest run output:

``` command
guild cat --output | guild run train --test-output-scalars -
```

Test output scalar rules interactively (i.e. type sample output to evaluate and press **Enter**):

``` command
guild run train --test-output-scalars -
```

Test flag imports:

``` command
guild run train --test-flags
```

Stage a run to examine its file layout:

``` command
guild run train --stage --run-dir /tmp/staged-run
```
