<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

This document describes the assumptions that Guild makes in the absence of explicit configuration.

In general, Guild must know the following about an operation:

- [Flags interface](/docs/flags#flags-interface)
- [Flag definitions](/docs/flags#flag-definitions)
- [Output scalars](/docs/scalars/#output-scalars)

If this information is not defined explicitly in a [Guild file](/docs/guildfiles), Guild attempts to infer the information using rules based on what you run.

## Python Scripts

Unless otherwise configured in a Guild file, Guild makes assumptions when running Python scripts. This includes cases when a script is run directly and when a script is defined using the `main` operation attribute.

### Flags Interface

If [`flags-dest`](/reference/guildfile#operation-flags-dest) is not defined for an operation, Guild attempts to detect the interface by inspecting the Python module.

- If the module imports the [`argparse`](https://docs.python.org/library/argparse.html), Guild assumes that flags are set using command line arguments and uses `args` for `flags-dest`.

- If the main module does not import `argparse`, Guild assumes that flags are defined in global variables and uses ``globals`` for `flags-dest`.

If you set `flags-dest` for an operation, Guild inspects the Python main module to infer the flags interface.

#### Example: Command Line Arguments

Consider the following Python module `train`:

``` python
import argparse

p = argparse.ArgumentParser()
p.add_argument("--learning-rate", type=float, default=0.1)
p.add_argument("--batch-size", type=int, default=100)

args = p.parse_args()

# Use args to train model, etc.
```

Unless `flags-dest` is configured for the operation, Guild inspects the module and detects the import of `argparse` and uses `args`.

#### Example: Global Variables

The following version of `train` does not import `argparse`. It defines flags as global variables.

``` yaml
learning_rate = 0.1
batch_size = 100

# Use globals to train model, etc.
```

Unless otherwise configured, when Guild inspects this module, it uses
``globals`` as the value for `flags-dest`.

``` yaml
train:
  flags-dest: globals
```

### Flag Imports

Once Guild determines the [flags interface](#flags-interface) for a Python module (see above), it tries to import flag definitions. The import method depends on the interface.

While you cannot control how Guild imports flags, you can control what flags are imported, if any.

By default, Guild imports all detected flags.

For details on controlling flag imports, see [Import Flags](/docs/flags#import-flags).

## Output Scalars

By default, Guild looks for scalar values in script output. It does this regardless of the language type.

Guild detects patterns in the format: <code><em>KEY</em>: <em>VALUE</em></code>, where *`KEY`* is a scalar identifier that occurs at the start of a line and *`VALUE`* is a valid float represenation. Guild logs these key/value pairs as *scalars*.

You can test Guild's current output scalar configruation by running the operation with the `--test-output-scalars` option.

If your script prints scalar values in a different format, you can control the pattern that Guild uses by defining the [`output-scalars`](/reference/guildfile#operation-output-scalars) attribute for an operation.

Refer to [Output Scalar](/docs/scalars#output-scalars) for more information.
