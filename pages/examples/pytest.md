<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

This [example](https://github.com/guildai/guildai/tree/master/examples/pytest) illustrates how pytest can be used within a Guild enabled project.

Project files:

|||
|-|-|
| [guild.yml](https://github.com/guildai/guildai/blob/master/examples/pytest/guild.yml) | Project Guild file |
| [demo.py](https://github.com/guildai/guildai/blob/master/examples/pytest/demo.py) | Project implementation |
| [cli.py](https://github.com/guildai/guildai/blob/master/examples/pytest/cli.py) | Project CLI |

## Using pytest

As Guild runs any Python project unmodified, you're free to use any variety of test frameworks including [pytest](https://docs.pytest.org/).

In this example, tests are implemented in the same module containing the test targets: [demo.py](https://github.com/guildai/guildai/blob/master/examples/pytest/demo.py). You're free to implement tests however in other ways, including separate modules and packages.

Here's a test function `prepare_data`:

<div data-guild-github-select="16-23">

https://github.com/guildai/guildai/blob/master/examples/pytest/demo.py#L20
</div>

You can run tests directly using the `pytest` command:

``` command
pytest demo.py
```

## Running tests from Guild

A private operation `_check` is implemented in [guild.yml](https://github.com/guildai/guildai/blob/master/examples/pytest/guild.yml):

<div data-guild-github-select="19-20">

https://github.com/guildai/guildai/blob/master/examples/pytest/guild.yml#L19
</div>

This simply invokes `pytest` to run the applicable tests for the project.

Note that this approach preserves project functionality: you can still run tests independently of Guild. By using Guild, you can record the results of a test associated with a snapshot of the source code. This is typically a function of CI (continuous integration) tests, which are run from source code commits. This nonetheless shows how simple it is to integrate tests from a another framework into Guild.
