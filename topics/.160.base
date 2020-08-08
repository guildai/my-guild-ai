<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

Scalars are numeric values that are logged during a run. Scalars are used to log metrics like accuracy and loss.

A scalar value is associated with a *key* and a *step*. A scalar step denotes the training step or epoch associated with a value. In cases where a step does not apply, the step is `0`.

Scalars may be logged using one of two methods:

- Writing values to script output
- Explicit logging of TensorBoard summaries

A scalar that is written to script output is known as an *output scalar*. For more information, see [Output Scalars](#output-scalars) below.

TensorBoard summaries are written to files supported by [TensorBoard](https://www.tensorflow.org/tensorboard) and other machine learning tools. For more information, see [TensorBoard Summaries](#tensorboard-summaries) below.

## Output Scalars

By default, Guild logs for scalars in script output in the format `key: value` where each value is written on a single line without leading whitespace. Guild sets the current scalar step when the `step` key is used. Subsequently logged values are associated with the latest step.

The following output generates a series of 3 scalar values for `loss`:

``` output
step: 1
loss: 0.1
step: 2
loss: 0.05
step: 3
loss: 0.01
```

<span data-guild-class="caption">Sample output --- compatible with Guild's default output scalar logging</span>

In this case, the logged scalar values are:

| **key** | **value** | **step** |
|---------|-----------|----------|
| loss    | 0.1       | 1        |
| loss    | 0.05      | 2        |
| loss    | 0.01      | 3        |

You can modify the way Guild logs output scalars using the `output-scalars` operation attribute in a [Guild file](/docs/guildfiles).

Consider the following output:

``` output
Epoch 1/3
- loss: 0.5 - accuracy: 0.8
Epoch 2/3
- loss: 0.1 - accuracy: 0.9
Epoch 3/3
- loss: 0.05 - accuracy: 0.95
```

The default pattern `key: value` does not work in this case. To capture scalars for this output, define `output-scalars` as follows:

``` yaml
train:
  output-scalars:
    - step: 'Epoch (\step)'
    - '- (\key): (\value)'
```

Refer to [*Guild File Reference*](/reference/guildfile#output-scalars) for a specification of the `output-scalars` attribute.

Refer to [*Guild File Cheatsheet*](/cheatsheets/#output-scalars) for examples of `output-scalars`.

## TensorBoard Summaries

Guild detects scalars logged to TensorBoard summaries.

If you log scalars to TensorBoard summaries, disable output scalar logging by setting `output-scalars` to `off`.

``` yaml
op:
  output-scalars: off
```

You can log TensorBoard summaries using various Python APIs.

| *Python API* | *When to Use* |
|-|-|
| [TensorFlow API](https://www.tensorflow.org/api_docs/python/tf/summary) | Operation uses TensorFlow or Keras |
| [PyTorch API](https://pytorch.org/docs/stable/tensorboard.html) | Operation uses PyTorch |
| [MXBoard](https://github.com/awslabs/mxboard) | Operation uses MXNet |
| [tensorBoardX](https://github.com/lanpa/tensorboardX) | Log TensorBoard summaries without incurring a large framework dependency |

> <span data-guild-class="callout tip">Tip</span> [tensorBoardX](https://github.com/lanpa/tensorboardX) is a light-weight library that is not tied to a large framework like TensorFlow or PyTorch. Consider it if you don't otherwise have access to a summary logging API.

## View Run Scalars

Show runs scalars using [`guild runs info`](/commands/runs-info).

By default, Guild omits scalars starting with `sys/` as these scalars are systems-related can overwhelm the list of scalars. To include system scalars, use the `--all-scalars` option:

``` command
guild runs info --all-scalars
```

You can also view scalar values in TensorBoard in the **Scalars** tab.

``` command
guild tensorboard --tab scalars
```

To show all scalars for multiple runs, use the `--print-scalars` option with [`guild compare`](/commands/compare).

``` command
guild compare --print-scalars
```
