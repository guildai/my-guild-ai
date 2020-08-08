<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

This guide provides details for using and configuring Guild on macOS.

## Z Shell (zsh)

[Z Shell (zsh)](https://en.wikipedia.org/wiki/Z_shell) is the default command line shell for macOS. If you're using `zsh` you must quote arguments that contain square brackets --- `[` and `]`. If you don't, you see a cryptic error message `zsh: no matches found: ...`.

For example, use this format:

``` command
guild run learning-rate='[0.001,0.01,0.1]'
```

<span data-guild-class="caption">When using zsh, quote arguments that contain square brackets.</span>

If you're not using Z Shell, you can omit the quotes.

Alternatively, when running Z Shell you can alternatively use the `noglob` keyword to disable glob replacement. This lets you use unquoted arguments containing square brackets.

``` command
noglob guild run learning-rate=[0.001,0.01,0.1]
```

<span data-guild-class="caption">`noglob` lets you use unquoted square brackets.</span>

To use `noglob` whenever running Guild operations, [create an alias](https://stackoverflow.com/questions/8967843/how-do-i-create-a-bash-alias) like this:

```
alias guild='noglob guild'
```
