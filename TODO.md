# To Do

## Work on next

- Identify areas needing work with TODO (search works well)
- Link scanner?
- Fix links

## Topics

### Things to Replace/Check

- '^ ...' -> <span data-guild-class="caption">...</span>
- [...](xxx:yyy)
- '!!! ...' ->
    - <span data-guild-icon="info-circle" data-guild-class="callout info"></span>
    - <span data-guild-icon="info-circle" data-guild-class="callout note"></span>
    - <span data-guild-icon="check-circle" data-guild-class="callout tip"></span>
    - <span data-guild-icon="exclamation-circle" data-guild-class="callout important"></span>
    - <span data-guild-icon="thumbs-up" data-guild-class="callout highlight"></span>

- cmd:xxx -> /commands/xxx + fixed formatting
- URL fragments inside permalinks -> use topic URLs to avoid redirects
- Avoid italics for references to docs and sections
- Avoid periods in captions
- Refer use of <var> and go back to VAR - this is consistent with
  naming conventions used in command help
- ``xxx`` -> `xxx`
- Find /terms/xxx and make sure we have permalinks to those

### Consolidate Guildfile Cheatsheets

- Move to single doc
- Remove extra permalinks
- Update an links

### www-pre -> main site on launch

### Fill in Examples

We lost the examples index. Need to fill out the content on my.guild.ai/examples.

### See Also

Lots of opportunities to specify "See also" references.

### Nice to Have

Some command formatting is wonky. Spacing around "Examples" for dates,
etc.

### Guild AI Tweaks component

- CSS
- Move to GitHub when it's stable

### TOC Component

### Related Links and See Other Links

Once content is stabilized, fill in with cross references.

### Try to format commands and output with darker background color.

At least with a darker background it's suggestive of a terminal.

Even better would to support the `$` chrome.

### Glue docs together

This might be a TOC or Index. I'm guessing this would need to be a
banner?

Also, how to navigate through the docs.

Solid progress by simply ordering categories.

### Permalinks

All docs and categories need permalinks.

### Transfer docs over

### Cleanup main site to point here

### Cleanup links

Once we have the site structure settled we need to go through
everything and fix `cmd`, `ref` and `term` links.

### Integrated chat

It'd be nice to provide a real time experience for resolving issues
with users. Slack has been great for this.

Approaches:

- Use a chat built into Discourse. Is there such a thing?
- Integrate with Slack somehow.

### Splash content on front page

Visiting anonymously shows unstructured categories. We need something
to provide a good starting point.

Scenarios:

- Curious about Guild - send to main site
- Link to get started
- Link to docs

### Scheme to customize CSS without losing changes

### Header links

Consider this theme component:

https://meta.discourse.org/t/brand-header-theme-component/77977

### File tree widget

Nested unordered lists are rending meekly. How to show a formated tree
structure?

### Apply consistent formatting

- Fig/table captions indented and italicized
- Avoid italics for links - or come up with a consistent rule - it
  seems inconsistent in the upstream docs

### Solution checkbox

In meta.discourse.org they offer a "Solution" checkbox, which
designates a reply as a solution to a question. I think this would be
useful on #general and #troubleshooting (possibly not others though).

### Links for examples

Bring over some of the better examples. But what?

How do we deal with sync bewteen my.guild.ai and the GitHub repo?

I think maybe we want to sync those with `my-guild` tool. E.g.

    $ my-guild publish-example <name>

E.g. grab the README.md from GitHub and use it to generate post
content for my.

We'd want to follow the same support for commands I think.

This can go in after 0.7 ships.

OR, modify README to point to the docs on my. This is better I think.

## Done

### "Copy" code button

I saw this on meta.discourse.org so it should be possible.
