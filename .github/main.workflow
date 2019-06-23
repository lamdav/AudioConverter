workflow "test and publish on tag" {
  on = "push"
  resolves = ["pypi"]
}

action "black" {
  uses = "./.github/actions/black"
}

action "tag-filter" {
  needs = [
    "black"
  ]
  uses = "actions/bin/filter@master"
  args = "tag"
}

action "pypi" {
  needs = "tag-filter"
  uses = "./.github/actions/pypi"
  secrets = ["TWINE_USERNAME", "TWINE_PASSWORD"]
}
