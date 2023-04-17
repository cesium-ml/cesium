# How to Contribute

We gratefully accept contributions of new time-series features, be they domain-specific or general.

## License

cesium is released under the Modified BSD license, which means that you are allowed to modify the code for your own purposes, as long as you retain our [copyright notice](https://github.com/skyportal/skyportal/blob/main/LICENSE.txt).

However, we would love to grow the cesium community, and integrate improvements directly into our [code repository on GitHub](https://github.com/cesium-ml/cesium).

## Including your changes

To make a code contribution to the project, follow these steps (which
are outlined in more detail in [this GitHub
guide](https://guides.github.com/activities/forking/)):

1. Make a fork of the [cesium repository](https://github.com/cesium-ml/cesium)
2. Clone your fork, and add `upstream` (`git@github.com:cesium-ml/cesium`) as a remote
3. Create a new branch and add your feature
4. Submit a pull request (PR) on GitHub

The other developers will provide feedback, and you may push updates
into the same branch (which will also update your pull request), until
the Continuous Integration tests pass and reviewers agree that it
should be merged (see "Process Guidelines: Reviews" below).

For a more detailed explanation of the open contribution process, see
the [scikit-image contributors' guide](http://scikit-image.org/docs/stable/contribute.html).
We follow a very similar process; some guidance follows below.

### Adding new time-series features

To add your time-series features to the project, please follow the guidelines below:

  1. Add your code to a new or existing file in `cesium/features/`.
  2. In `cesium/features/graphs.py`, add your features to the
    `dask_feature_graph`.
  3. Add your features to the `feature_categories` & (optionally)
   `feature_tags` dictionaries in `cesium/features/graphs.py`.
  4. Write tests for your new features (see below).

Notes:

  - The keys `'t'`, `'m'`, and `'e'` refer to the time series times,
    measurements, and errors respectively.
  - More complicated operations which re-use intermediate values can be
    constructed via standard `dask` graph syntax: see the [`dask`
    documentation](http://dask.pydata.org/en/latest/custom-graphs.html) for
    details, or the feature `freq1_freq` in `graphs.py` as an example.

## Bug Reports

While we appreciate code changes, it is also very helpful simply to
know when cesium does not function correctly.  Please [file any
issues](https://github.com/cesium-ml/cesium/issues) you run across.

If possible, provide:

1. A full description of your environment, including operating system,
   and Python version.
2. A minimal way to reproduce the problem you see; these can be either
   a set of instructions, or a script.

## Process guidelines

Because many developers work on cesium, and PRs sometimes come in
at a rapid pace, we have guidelines to streamline review and
development:

### Code style

We don't like arguing about code style, and likely you don't
either. Therefore, we use code formatters: black for Python, and
Prettier for JavaScript.  Code is an art, and opinions differ of what
looks good: we choose to spend our time writing correct, elegant code.

### Testing

All functionality should be accompanied by tests.  We use pytest.
PRs can only be merged once tests have
been added and pass.  The continuous integration system indicates this
with a green checkmark, hence you may see developers talking about "PR
599 being green" ✅.

### Reviews

All code that goes into cesium is reviewed by at least one team member
(team members are persons with commit access) or, if the contributor
is a team member, by at least one other team member.  We find review
invaluable for improving code quality, and no author ever merges their
own work.

We ask all reviewers to be mindful that there is a human at the other
side of the PR.  As such, consider the review process as a
conversation aimed at getting the work mergeable as quickly as
possible:

- Do not nitpick in comments; add small fixes as suggestions (click
  the `±` button) or push uncontroversial changes as a commit into the
  PR branch.  We prefer suggestions, because that still gives the
  original author a chance to accept/reject the change.

- Comments should provide actionable feedback, and can come in
  two flavors: suggestions and requirements.  Requirements are direct
  instructions such as "Define the variable first", whereas
  suggestions are softer: "Consider whether you'd like to reformat
  this dictionary" or "Recommendation: prefer the shorthand form".

- When comments are left on your PR, let the reviewer resolve their
  comments once they are satisfied they've been adequately addressed
  (unless you've done exactly as they asked).

### Focused PRs

In cesium, we squash all PRs before merging them.  Because of this,
it is okay to merge the main branch into your branch, instead of
rebasing.

The resulting squashed commit should deal with one topic only.  For
example, if you find that, while implementing a new component, you
also need to fix another, split that out into a separate PR.

Long PRs take much longer to review than shorter ones.  So, for the
benefit of the developer and reviewers alike, we ask that PRs are kept
as small as possible.

### Describe your work

When a PR is squashed, all commit messages are listed.  Please provide
information in commit messages on what they do—this helps us
track bugs down later.  A commit message has a title and a
description:

```
Return JSON when accessing invalid API endpoint (#644)

Currently, the main page gets rendered for invalid API endpoint requests
(i.e., `/api/*` where `*` is invalid). Now, it returns 400 as JSON with an
error message in the `message` field.
```

The description may be ommitted for small fixes.

Remember that you can augment the last commit using `git commit
--amend`, instead of making numerous `Also fixed x` type commits.

### Very large, dependent sets of changes

Sometimes, you are working on a feature that is large enough that it
spans several sequential PRs.  In this case, each branch will depend
on the previous, so you may have:

- `part-1` (based on main)
- `part-2` (based on feature-part-1)
- `part-3` (based on feature-part-2)

etc.  Turn `part-1` into a PR and, once it is merged, move on to
`part-2`.  If you would also like others to look at `part-2` while
`part-1` is still under review, make a PR onto your own `part-1`
branch, and direct reviewers there.

## Git tips

- `git reflog` shows you the history of branch switches
- `git reset origin/main && git add --all` squashes your branch into a single commit
- `git add -p` adds only certain changes inside a file
