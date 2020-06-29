<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

Up to this point, you run `train.py` directly without providing additional information about the script.

When Guild runs an operation, it determines the following:

- How the script reads user-provided values, or [*flags*](/docs/flags)
- How the script communicates numeric results, or [*scalars*](/docs/scalars), such as training *loss* and *accuracy*

Unless configured otherwise, Guild uses [default rules](/docs/defaults) to determine this information.

You can configure this information explicitly using a [*Guild file*](/docs/guildfiles). A Guild file is a human-readable text file named `guild.yml` located in a project directory.

## Create a Guild File

In the `guild-start` project directory, create a file named `guild.yml` that contains this YAML code:

``` yaml
train:
  description: Sample training script
  main: train
  flags-import: all
  output-scalars: '(\key): (\value)'
```

<span data-guild-class="caption">Project Guild file `train.yml`</span>

The project directory should look like this:

> <span data-guild-class="ls-dir-open">guild-start</span>
<span data-guild-class="ls-dir ls-1">archived-runs</span>
<span data-guild-class="ls-file ls-1">guild.yml</span>
<span data-guild-class="ls-file ls-1">train.py</span>

The Guild file defines how Guild runs the `train` operation.

Below is a description of each setting.

<div data-guild-class="terms">

|||
|-|-|
| `description` | This value appears when listing the operation and in project help. See [*Get Project Info*](#get-project-info) below. |
| `main` | Guild loads the specified Python module when running the operation. By default, Guild uses the operation name. We could omit `main` in this case but include it here to illustrate its use. For more information, see [*Python Based Operations*](/docs/operations#python-based-operations). |
| `flags-import` | When a Guild file is used, Guild does not automatically import flags from the main module. You must explicitly import flags or define them for the operation. In this case, we tell Guild to [import all detected flags](/docs/flags#import-all-flags) from the main module. |
| `output-scalars` | Numeric results like *loss* and *accuracy* are called [*scalars*](/docs/scalars). Guild detects scalars written as script output (e.g. using `print` or `log` functions in Python) and those that are [logged explicitly](/docs/scalars#tensorboard-summaries). By default, Guild captures scalars written to output in the format <code><em>KEY</em>: <em>VALUE</em></code>. We could omit `output-scalars` in this case but include it here for illustration. For more information, see [*Output Scalars*](/docs/scalars#output-scalars). |

</div>

Refer to [*Guild File Reference*](/reference/guildfile) for details about the Guild file format and available configuration options.

> <span data-guild-class="callout note">Note</span> The values for `flags-import` and `output-scalars` used in the Guild file above are equivalent to the defaults used by Guild. They can be omitted without changing the behavior of the operation. We define them here for illustration purposes.

## Get Project Info

Save your changes to `guild.yml` above. Use [`guild operations`](/commands/operations) to show operations defined for the project:

``` command
guild operations
```

``` output
train  Sample training script
```

Use [`guild help`](/commands/help) to show project information:

``` command
guild help
```

[details="Output"]
``` output
OVERVIEW

    You are viewing help for operations defined in the current directory.

    To run an operation use 'guild run OPERATION' where OPERATION is one
    of options listed below. If an operation is associated with a model,
    include the model name as MODEL:OPERATION.

    To list available operations, run 'guild operations'.

    Set operation flags using 'FLAG=VALUE' arguments to the run command.
    Refer to the operations below for a list of supported flags.

    For more information on running operations, try 'guild run --help'.
    For general information, try 'guild --help'.

BASE OPERATIONS

    train
      Sample training script

      Flags:
        noise  (default is 0.1)
        x      (default is 0.1)

```
[/details]

Press **q** to exit help.

> <span data-guild-class="callout highlight">Highlight</span> In addition to configuring operations, Guild files define the *user interface* for a project. The interface is discovered with Guild commands like [`operations`](/commands/operations) and [`help`](/commands/help). This supports project reuse and reproducibility. Operations are easy to recall, run, and compare.

## Run the Operation

Run the `train` operation:

``` command
guild run train
```

``` output
You are about to run train
  noise: 0.1
  x: 0.1
Continue? (Y/n)
```

> <span data-guild-class="callout important">Important</span> Use `train` rather than `train.py` here. `train` (without the `.py` extension) is the operation defined in the Guild file. `train.py` (with the extension) refers to the Python script directly. Guild supports both methods: running operations defined in Guild files and running scripts directly.

Press **Enter** to start the operation.

Guild runs `train`, which is equivalent to the operations you've run to this point, but is explicitly defined in `guild.yml`.

> <span data-guild-class="callout tip">Tip</span> While it's convenient to run scripts directly in Guild, we recommend that you use a Guild file to explicitly define operations for your day-to-day workflow. Guild file operations are configured explicitly and discoverable as show above. They support a wide range of features that are not available when running scripts directly. For more information, see [*Guild File Reference*](/reference/guildfile).

## Summary

In this section, you create a Guild file to explicitly define a `train` operation.

> <span data-guild-class="callout highlight">Highlights</span>
> - Guild files let you control and customize Guild support without modifying your code. This ensures that your code and your tools remain independent.
>- Guild files let you and your colleagues more effectively use a project because operations are well-defined and discoverable.

In the next section, you create a real-world classifier and use Guild to track and compare results.

<span data-guild-class="btn next">[Next: Add a Classifier](/start/classifier)</span>
