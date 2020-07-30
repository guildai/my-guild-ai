# my.guild.ai

## Setup

Install this toolkit by running:

```
python setup.py develop
```

## Process

### Refresh All Commands

Do this on a new feature release or when the command template changes.

IMPORTANT: The published commands will reflect the currently installed
version of Guild. Be certain to check out the appropriate commit/tag
when generating command help from a source code based version of
Guild.

    $ cd ~/SCM/guild
    $ git checkout VERSION-TAG

Clear the my-guild cache.

    $ cd ~/SCM/my-guild-ai
    $ my-guild clear-cache --all

Publish the commands.

    $ my-guild publish-docs

## CLI

Run `my-guild --help` for help.

## Doc Templates

### Doc Header

```
<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>
```

### Callouts

```
> <span data-guild-icon="info-circle" data-guild-class="callout info"></span> ...
> <span data-guild-icon="info-circle" data-guild-class="callout note"></span> ...
> <span data-guild-icon="check-circle" data-guild-class="callout tip"></span> ...
> <span data-guild-icon="exclamation-circle" data-guild-class="callout important"></span> ...
> <span data-guild-icon="thumbs-up" data-guild-class="callout highlight"></span> ...
```

### Captions

```
<span data-guild-class="caption">...</span>
```

- Avoid using periods to terminate captions. Instead use dashes or
  semicolons to make compound statements. Uperiods only when a caption
  must use multiple sentences.

### Commands

```
[`guild runs`](/commands/run)
```

- Do not use "the [guild run](/commands/run) command" but instead use
  "[guild run](/commands/run)".
