<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

The examples below apply to Guild [user configuration](/reference/user-config). For a complete reference of remote configuration, see [Remotes Reference](/reference/remotes).

## SSH

The following is a minimal SSH remote configuration. Runs are located on the remote host under the Guild home `~/.guild` where `~` is the home directory for the default user associated with `remote-hostname`.

``` yaml
remotes:
  ssh-remote:
    type: ssh
    description: Remote runs
    host: remote-hostname
```

Note that `ssh` defaults are specified according to the SSH implementation on the local (client) system. Refer to the documentation for your SSH client for details on configuring defaults.

The next example defines additional SSH settings as well as a Guild environment.

``` yaml
remotes:
  production:
    type: ssh
    description: Production runs
    host: remote-hostname
    user: ubuntu
    port: 2222
    guild-env: ~/Envs/production
    init: test -e ~/Envs/production || guild init -y ~/Envs/production
```

Note that `init` defines a command that creates a Guild environment if one doesn't exist. Use `guild remote start production --reinit` to ensure that the environment is setup correctly before running Guild commands.

## EC2

The following is a minimal example of an EC2 remote:

``` yaml
remotes:
  ec2-v100:
    type: ec2
    description: NVIDIA V100 on EC2
    region: us-east-2
    ami: ami-0a47106e391391252
    instance-type: p3.2xlarge
    public-key: ~/.ssh/id_rsa.pub
    user: ubuntu
```

## S3

The following example stores runs directly in `my-s3-production-runs` bucket.

``` yaml
remotes:
  s3-production:
    type: s3
    description: Production runs
    bucket: my-s3-production-runs
```

You can use `root` to store runs under a bucket path.

``` yaml
remotes:
  s3-test:
    type: s3
    description: Test runs
    bucket: my-s3-runs
    root: test

  s3-production:
    type: s3
    description: Production runs
    bucket: my-s3-runs
    root: production
```

## Azure VM

The following is a minimal example of an Azure VM remote:

``` yaml
remotes:
  azure-debian:
    type: azure-vm
    description: Debian VM
    image: Debian:debian-10:10:latest
    instance-type: Standard_DS1_v2
    disk-type: Premium_LRS
    public-key: ~/.ssh/id_rsa.pub
    user: azureuser
```

## Azure Blob

The following example stores in the `default` folder in the specified container. Note that `root` is optional.

``` yaml
remotes:
  azure-dev:
    type: azure-blob
    description: Development runs
    container: https://myco.blob.core.windows.net/guild-dev-runs
```

## Gist

The following example stores runs in a GitHub gist for user `jack`. The gist is identified using a specially named Guild README file containing the gist name `shared-runs`.

``` yaml
remotes:
  shared:
    type: gist
    user: jack
    gist-name: shared-runs
```

To write to this gist, specify a gist-authorized personal access token with the environment variable `GIST_ACCESS_TOKEN`.
