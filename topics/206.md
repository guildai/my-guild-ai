<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

This [example](https://github.com/guildai/guildai/tree/master/examples/languages) shows how Guild works with various runtime languages.

Project files:

|||
|-|-|
| [guild.yml](https://github.com/guildai/guildai/blob/master/examples/languages/guild.yml) | Project Guild file |
| [train.r](https://github.com/guildai/guildai/blob/master/examples/languages/train.r) | R example |
| [train.sh](https://github.com/guildai/guildai/blob/master/examples/languages/train.sh) | Bash example |
| [train-2.sh](https://github.com/guildai/guildai/blob/master/examples/languages/train-2.sh) | Alternative Bash example using environment variables |
| [Train.java](https://github.com/guildai/guildai/blob/master/examples/languages/Train.java) | Java example |
| [train.jl](https://github.com/guildai/guildai/blob/master/examples/languages/train.jl) | Julia example |

## Flag Interfaces

Guild uses two general interfaces to pass flag values to programs:

- Command line arguments
- Environment variables

The examples in this project show the use of both. Refer to the sections below for details.

When using a command line interface, flag values may be referenced in arguments using <code>${<em>FLAG_NAME</em>}</code>.

To include all flag arguments, use `${flag_args}`. In this case, each flag is included as two arguments in the format <code>`--`<em>FLAG_ARG_NAME</em> <em>FLAG_VALUE</em></code>.

## Source Code

Operations are run in the context of a *run directory*, not the project directory. Required files must be copied or linked into the run directory using one of two methods:

- Source code copy, which Guild performs automatically
- File dependency

In the case of scripts, examples reference copied source code using the pattern `.guild/sourcecode/<script>`.

## R Example

https://github.com/guildai/guildai/blob/master/examples/languages/guild.yml#L1-L8

https://github.com/guildai/guildai/blob/master/examples/languages/train.r

<span data-guild-class="caption">R port of the sample function used in [Get Started with Guild AI](/start)</span>

Run this example:

``` command
guild run r
```

Press `Enter` to run the sample training operation using the default values.

## Bash Examples

There are two examples that use Bash scripts:

|||
|-|-|
| `bash` | Uses command line arguments to pass flag values |
| `bash-2` | Uses environment variables to pass flag values |

Both examples print flag values and exit without doing any work. They serve as patterns for scripts in any language.

### Bash with Command Line args

https://github.com/guildai/guildai/blob/master/examples/languages/guild.yml#L10-L15

https://github.com/guildai/guildai/blob/master/examples/languages/train.sh

Run this example:

``` command
guild run bash
```

### Base with Environment Variables

https://github.com/guildai/guildai/blob/master/examples/languages/guild.yml#L17-L26

https://github.com/guildai/guildai/blob/master/examples/languages/train-2.sh

Run this example:

```
$ guild run bash-2
```

## Java Example

The Java examples uses a Bash command to compile Java source code and then run the compiled code.

https://github.com/guildai/guildai/blob/master/examples/languages/guild.yml#L28-L35

https://github.com/guildai/guildai/blob/master/examples/languages/Train.java

Run this example:

``` command
guild run java
```

## Julia Example

The Julia example requires the `ArgParse` modules. If it's not installed, you can install it from the Julia command line by running:

``` command2
julia> import Pkg
julia> Pkg.add("ArgParse")
```

https://github.com/guildai/guildai/blob/master/examples/languages/guild.yml#L37-L44

https://github.com/guildai/guildai/blob/master/examples/languages/train.jl

<span data-guild-class="caption">Julia port of the sample function used in [Get Started with Guild AI](/start)</span>

To run the Julia example:

``` command
guild run julia
```
