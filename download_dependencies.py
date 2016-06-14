import json
from os import path
from subprocess import call

def list_deps(root_dir='.'):
	deps = {}
	dep_fn = path.join(root_dir, "module.json")

	if not path.exists(dep_fn):
		return deps

	mbed_target_deps = {}
	with open(dep_fn, "r") as fd:
	    parsed_json = json.load(fd)

	    deps = parsed_json.get("dependencies", dict())
	    target_deps = parsed_json.get("targetDependencies")
	    test_deps = parsed_json.get("testDependencies", dict())

	    deps.update(test_deps)

	    if target_deps != None:
	    	mbed_target_deps = target_deps.get("mbed-os", dict())

	deps.update(mbed_target_deps)

	for dep_name, dep_url in deps.items():
		if '/' not in dep_url:
			print dep_name, dep_url, "does not point to github, automatic installation not supported"
			deps.pop(dep_name)
		if path.exists(path.join(root_dir, dep_name+".lib")):
			print dep_name, "managed by mbed-os, removing"
			deps.pop(dep_name)

	return deps

def fetch_deps(deps, working_dir='.'):
	target_repo_dirs = []
	for dep_name, dep_url in deps.iteritems():
		github_url = "git@github.com:{}.git".format(dep_url)
		target_repo_dir = path.join(working_dir, dep_name)
		target_repo_dirs.append(target_repo_dir)
		if path.isdir(target_repo_dir):
			print target_repo_dir, "already exist, skipping"
			continue

		cmd = ['git', 'clone', "--depth", "1", github_url, target_repo_dir]
		print "fetching:", github_url
		retval = call(cmd)
		assert(retval == 0)

	return target_repo_dirs

if __name__ == "__main__":
	deps = list_deps()
	while True:
		fetched_repos = fetch_deps(deps)
		old_keys = deps.keys()
		for fetched_repo in fetched_repos:
			deps.update(list_deps(fetched_repo))
		print deps
		if deps.keys() == old_keys:
			break
