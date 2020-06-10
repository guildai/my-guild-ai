# my.guild.ai

## Command Help Topics

Use the following for auth:

    $ source <( gpg -d api-creds.gpg )

Commands:

```
Usage: myguild [OPTIONS] COMMAND [ARGS]...

  Support for managing my.guild.ai.

  Commands that access my.guild.ai (publishing, etc.) require the
  environment variable MY_GUILD_API_KEY. If this variable is not set, the
  commands exits with an error.

  Refer to help for the commands below for more information.

Options:
  --debug  Enable debug logging
  --help   Show this message and exit.

Commands:
  publish-command  Publish command help to a topic.
  publish-index    Publish command index.
  sync-commands    Synchronize command help.

```

Use `publish-command` to publish a single command. Support preview.

    $ my-guild publish-command [CMD]

Use `sync-commands` to sync all commands. Note this does not detect
deleted commands. Deleted commands must be removed manually.

Use `publish-index` to generate an up-to-date index and publish it
under [`guild-commands`](https://my.guild.ai/t/guild-commands) topic.
