<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

Guild user configuration can be specified using one of three methods:

- In `~/.guild/config.yml` (default)
- In `guild-config.yml` located in the current working directory (e.g. defined alongside `guild.yml` in a project)
- In a file specified by the `GUILD_CONFIG` environment variable (overrides the two previous methods)

> <span data-guild-class="callout note">Note</span> User configuration is defined using only one of these methods. If a project contains `guild-config.yml` it will be used instead of `~/.guild/config.yml`. In this case, if you want to use default configuration (i.e. defined in `~/.guild/config.yml`) use `GUILD_CONFIG=~/.guild/config.yml` in your command or copy the required settings to `guild-config.yml`.

The following sections document the type of information defined in user configuration.

## Check

**Section heading:** `check`

[`guild check`](/commands/check) can be configured by defining any of the attributes below under a top-level `check` mapping.

### Check Attributes

<div data-toc-id="check-offline"><h4>offline</h4></div>

*Flag specifying default offline mode for checks (boolean)*

When offline, Guild will not check for latest versions and will instead show `unchecked (offline)`.

Default is `no`.

### Check Examples

Don't check for latest Guild AI version by default:

``` yaml
check:
  offline: yes
```

Note, you can use `--offline` or `--no-offline` when running [`guild check`](/commands/check) to override this setting.

## Diff

**Section heading:** `diff`

[`guild diff`](/commands/diff) can be configured by defining any of the attributes below under a top-level `diff` mapping.

### Diff Attributes

<div data-toc-id="diff-command"><h4>command</h4></div>

*Command used when diffing two paths (string)*

Two paths are appended to this command as separate arguments --- one for each applicable run path.

### Diff Examples

Use [Meld](https://meldmerge.org/) to diff runs:

```
diff:
  command: meld
```

## Remotes

**Section heading:** `remotes`

Remotes provide configuration that Guild uses for remote-related operations. A remote operation is specified by using the `--remote` option with the name of remote configured in this section.

For example, the following command starts an operation on a remote named `my-host`:

```command
guild run train --remote my-host
```

In this case, `my-host` must be defined under `remotes` in user config:

``` yaml
remotes:
  my-host:
    ...
```

Refer to [Remotes Reference](/reference/remotes) for details on configuring remote types.
