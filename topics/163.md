<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

The term *pipeline* in this section refers to running multiple [operations](/docs/operations) to accomplish a goal.

Guild pipelines are implemented using higher-level operations, which define sub-operations using a [`steps`](/reference/guildfile#operation-steps) attribute.

Consider the following three operations:

``` yaml
prepare-data:
  description: Prepare data for train and test

train:
  description: Train a model
  requires:
    - operation: prepare-data

test:
  description: Test a model
  requires:
    - operation: prepare-data
    - operation: train
```

The pipeline implied by these operations is:

1. Run `prepare-data` to generate a data set that can be used for train and test.
2. Run `train` to train a model on prepared data.
3. Run `test` to test a model on prepared data.

You can run these operations manually as a part of your development process. For example, you might run `prepare-data` different times, each with different flags to experiment with different processing stages, feature engineering, etc. After each `prepare-data` you may run `train` to explore model validation performance. After iterating over data preparation and training, finally, you run `test` to measure your results against hold-out data set.

This process represents an ad-hoc pipeline.

When you want to automate a sequence of operations, create a higher-order operation using [`steps`](/reference/guildfile#operation-steps).

Consider a new operation `pipeline`:

``` yaml
pipeline:
  description: Runs model pipeline end-to-end
  steps:
   - prepare-data
   - train
   - test
```

When you run `pipeline`, Guild starts a higher-order operation, which runs each of the specified steps in the order specified.

## Step Flag Values

Specify flag values for a step in one of two ways:

- Arguments to the step operation name
- [`flags`](/reference/guildfile#step-flags) attribute of a [`run`](/reference/guildfile#step-run) object

For example, this examples uses flag arguments:

``` yaml
pipeline:
  steps:
   - train lr=0.01 epochs=100
   - test
```

This example uses a `flags` step attribute:

``` yaml
pipeline:
  steps:
    - run: train
      flags:
        lr: 0.01
        epochs: 100
    - test
```

### Expose Step Flag Values

To expose a step flag value to the user, define a flag for the pipeline operation and explicitly use it as a step flag.

``` yaml
pipeline:
  flags:
    train-lr: 0.01
    train-epochs: 100
  steps:
    - train lr=${train-lr} epochs=${train-epochs}
    - test
```

## Step Run Attributes

You may define a number of step run attributes when using step mapping. Refer to [*Guild File Reference*](/reference/guildfile#other-step-run-options) for details.
