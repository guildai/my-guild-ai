<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

This [example](https://github.com/guildai/guildai/tree/master/examples/hyperopt) illustrate how to create a custom optimizer using Hyperopt. Follow the patterns outlined below to use other sequential tuning algorithms with your project.

Project files:

|||
|-|-|
| [guild.yml](https://github.com/guildai/guildai/blob/master/examples/hyperopt/guild.yml) | Project Guild file |
| [train.py](https://github.com/guildai/guildai/blob/master/examples/hyperopt/train.py) | Sample training script |
| [tpe.py](https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py) | Optimizer support using Tree of Parzen Estimators with Hyperopt |
| [requirements.txt](https://github.com/guildai/guildai/blob/master/examples/hyperopt/requirements.txt) | List of required libraries |

An [*optimizer*](/docs/optimization) is a Guild operation that specializes in running multiple trials based on a batch prototype.

In this example, we create a custom optimizer named `tpe`. The optimizer is used to find optimal hyperparameter values using the Tree of Parzen Estimators algorithm from the [Hyperopt](http://hyperopt.github.io/hyperopt/) library.

Here's the Guild file that defines both the training operation and the optimizer:

https://github.com/guildai/guildai/blob/master/examples/hyperopt/guild.yml

> <span data-guild-class="callout note">Note</span> Each operation uses the Python module corresponding to its name. If a module uses a different name, specify it using the [`main`](/reference/guildfile#operation-main) attribute.

Start an optimization batch by running:

``` command
guild run train x=[-2:2] --optimize
```

The `train` operation is configured to use the `tpe` optimizer by default (see above).

The `tpe` optimizer is configured to run 10 trials by default. Change this value using `--max-trials`.

You can view operation help for `tpe` to show supported flags. These are set using `-Fo` options with [`guild run`](/commands/run).

``` command
guild run tpe --help-op
```

## Implementation

The `tpe` operation is implemented in [tpe.py](https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py).

Implementation conists of the following steps:

1. Read settings for the batch run and the batch *prototype*.
1. Convert prototype flag values into a Hyperopt [*search space*](https://github.com/hyperopt/hyperopt/wiki/FMin#2-defining-a-search-space)
1. Define a [*function to minimize*](https://github.com/hyperopt/hyperopt/wiki/FMin#1-defining-a-function-to-minimize) that runs a batch trial using hyperparameter values provided by Hyperopt.
1. Use Hyperopt [`fmin`](https://github.com/hyperopt/hyperopt/wiki/FMin) to start a sequential optimization process using the search space and function to minimize.

## Read Batch Settings

Use `batch_util.batch_run()` to get the current batch run. This is used to read the batch settings.

<div data-guild-github-select="23-26">

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L24
</div>

## Convert Prototype Flags to Search Space

The batch *proto* run defines the flag values used for trials. These may contain search specs like `[-2:2]` or `uniform[-2:2]`. This syntax represents a Guild [*search space function*](/docs/flags#search-space-functions). Decode search space functions to create a Hyperopt search space.

Read the proto flags and uses them to create a search space:

<div data-guild-github-select="68-70">

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L69
</div>

Decode each flag function to create a corresponding Hyperopt [search space expression](https://github.com/hyperopt/hyperopt/wiki/FMin#21-parameter-expressions):

<div data-guild-github-select="77-82">

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L79
</div>

## Function to Minimize

Hyperopt calls a function with a dictionary of suggested flag values. Use `batch_util.run_trial` to generate a trial for the batch using the suggested values:

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L48

The result is the objective specified in [`guild run`](/commands/run) --- or `loss` by default.

## Minimize the Objective

Call `fmin` to minimize the objective:

<div data-guild-github-select="29-37">

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L32
</div>

### Configure TPE Algorithm

The value for `algo` uses a local function that supports the TPE hyperparameters. The hyperparameters in this case are defined as module global variables. These are imported by Guild and can be customized using `-Fo` options with [`guild run`](/commands/run).

<div data-guild-github-select="109-112">

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L109
</div>

### Perform Summary Actions

This implementation labels the "best" run. Run any number of summary actions in your custom optimzer.

<div data-guild-github-select="116-119">

https://github.com/guildai/guildai/blob/master/examples/hyperopt/tpe.py#L116
</div>
