import yaml

with open("environment-unpinned.yaml", "r") as fp:
    env_unpinned = yaml.load(
        fp.read(),
        Loader=yaml.SafeLoader,
    )
with open("environment-unpinned-dev.yaml", "r") as fp:
    env_unpinned_dev = yaml.load(
        fp.read(),
        Loader=yaml.SafeLoader,
    )
with open("../environment.yaml", "r") as fp:
    env_pinned = yaml.load(
        fp.read(),
        Loader=yaml.SafeLoader,
    )

# Only pin explicit dependencies


def iterate_deps(xs, ys, accumulator):
    for x in xs:
        for y in ys:
            if x.split("=")[0] == y.split("=")[0]:
                accumulator.append(x)


deps_not_pip = []
deps_pip = []
iterate_deps(
    env_pinned["dependencies"][:-1],
    env_unpinned["dependencies"][:-1] + env_unpinned_dev["dependencies"][:-1],
    deps_not_pip,
)
iterate_deps(
    env_pinned["dependencies"][-1]["pip"],
    env_unpinned["dependencies"][-1]["pip"]
    + env_unpinned_dev["dependencies"][-1]["pip"],
    deps_pip,
)
pruned_dependencies = [
    *sorted(list(set(deps_not_pip))),
    {"pip": sorted(list(set(deps_pip)))},
]

# Update env_pinned with pruned dependencies
env_pinned["dependencies"] = pruned_dependencies
# We don't want the prefix line
env_pinned.pop("prefix")

with open("../environment.yaml", "w") as f:
    f.write(yaml.dump(env_pinned))
