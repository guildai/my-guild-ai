<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

An *optimizer* is a Guild operation that runs a [*batch*](/docs/runs#batches). A batch generates one or more *trial runs* or *trials*. Optimizers are able to suggest flag values to minimize or maximize an objective.

Below is a list of supported optimizers.

|                   |                                                               |
|-------------------|---------------------------------------------------------------|
| [gp](#gp)         | Sequential optimizer using Gaussian processes.                |
| [forest](#forest) | Sequential optimizer using decision trees.                    |
| [gbrt](#gbrt)     | Sequential optimizer using gradient boosted regression trees. |
| [random](#random) | Batch processor using randomly selected values.               |

Use the default optimizer for an operation by specifying the `--optimize` option with [`guild run`](/commands/run). The default optimizer can be defined for an operation using the [`optimizers`](/reference/guildfile#operation-optimizers) attribute. Guild uses the [`gp`](#gp) optimizer if one is not otherwise defined for an operation.

Specify a named optimizer with the `--optimizer` option to [`guild run`](/commands/run). A name may be one of the optimizers below or may be the name of an optimizer defined for the operation.

Optimizer flags are set using `--opt-flag` or `-Fo`. Optimizer flags are specified like other flags using the format `NAME=VALUE`.

To run the default optimizer for `train`:

``` command
guild run train --optimize
```

To use the `forest` optimizer:

``` command
guild run train --optimizer forest
```

For more examples, see [*Guild File Cheatsheet*](/cheatsheets/guildfile#optimizers).

## gp

Bayesian optimizer using Gaussian processes.

Refer to [skopt API documentation](https://scikit-optimize.github.io/stable/modules/generated/skopt.gp_minimize.html) for details on this algorithm and its flags.

Aliases: `gaussian`, `bayesian`

### gp Flags

<div data-toc-id="gp-acq-func"><h4>acq-func</h4></div>

*Function to minimize over the gaussian prior (default is `gp_hedge`)*

Choices:

|            |                                                         |
|------------|---------------------------------------------------------|
| `LCB`      | Lower confidence bound                                  |
| `EI`       | Negative expected improvement                           |
| `PI`       | Negative probability of improvement                     |
| `gp_hedge` | Probabilistically use LCB, EI, or PI at every iteration |
| `EIps`     | Negative expected improvement per second                |
| `PIps`     | Negative probability of improvement per second          |

<div data-toc-id="gp-kappa"><h4>kappa</h4></div>

*Degree to which variance in the predicted values is taken into account (default is `1.96`)*

<div data-toc-id="gp-noise"><h4>noise</h4></div>

*Level of noise associated with the objective (default is `gaussian`)*

Use `gaussian` if the objective returns noisy observations, otherwise specify the expected variance of the noise.

<div data-toc-id="gp-random-starts"><h4>random-starts</h4></div>

*Number of trials using random values before optimizing (default is `3`)*

<div data-toc-id="gp-xi"><h4>xi</h4></div>

*Improvement to seek over the previous best values (default is `0.05`)*

## forest

Sequential optimization using decision trees. Refer to [skopt API documentation](https://scikit-optimize.github.io/stable/modules/generated/skopt.forest_minimize.html) for details on this algorithm and its flags.

### forest Flags

<div data-toc-id="forest-kappa"><h4>kappa</h4></div>

*Degree to which variance in the predicted values is taken into account (default is `1.96`)*

<div data-toc-id="forest-random-starts"><h4>random-starts</h4></div>

*Number of trials using random values before optimizing (default is `3`)*

<div data-toc-id="forest-xi"><h4>xi</h4></div>

*Improvement to seek over the previous best values (default is `0.05`)*

## gbrt

Sequential optimization using gradient boosted regression trees.

Refer to [skopt API documentation](https://scikit-optimize.github.io/stable/modules/generated/skopt.gbrt_minimize.html) for details on this algorithm and its flags.

### gbrt Flags

<div data-toc-id="gbrt-kappa"><h4>kappa</h4></div>

*Degree to which variance in the predicted values is taken into account (default is `1.96`)*

<div data-toc-id="gbrt-random-starts"><h4>random-starts</h4></div>

*Number of trials using random values before optimizing (default is `3`)*

<div data-toc-id="gbrt-xi"><h4>xi</h4></div>

*Improvement to seek over the previous best values (default is `0.05`)*

## random

Batch processor supporting random flag value generation.

Values are selected from the search space distribution specified for each flag value.

This optimizer does not attempt to optimize an objective.

The random optimizers does not support any flags.
