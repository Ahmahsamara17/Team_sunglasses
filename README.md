# pwncollege challenge monorepo

This repository will one day contain all core pwn.college challenges.

The basic idea is that challenges are just directories in here, similar to how they're specified in dojos currently.
They'll be auto-built out of these directories, probably as docker files (though some nix stuff is another possibility), and deployed seamlessly.

# Repository structure

The repository structure is:

- `./$MODULE_ID/$CHALLENGE_ID`: each challenge is a directory, and multiple challenge directories make up a module
- `./$MODULE_ID/$CHALLENGE_ID/challenge`: this directory contains challenge artifacts (code, etc) that are used for building and deployment
- `./$MODULE_ID/$CHALLENGE_ID/tests_public`: unencrypted tests used to test challenge functionality before deployment and also to test community contributions via CI
- `./$MODULE_ID/$CHALLENGE_ID/tests_private`: encrypted tests used to ensure challenge solvability before deployment

# Decrypting the solutions

The solutions and other private testcases in this repository are encrypted with [git-crypt](https://github.com/AGWA/git-crypt).
To decrypt them, you will need to:

```
git crypt unlock /path/to/keyfile 
```

Each module has its own keyfile that you'll need to be given to see/modify solutions for that module.
Alternatively, if your GPG key has been granted access to a solution key, you can just do:

```
git crypt unlock
```

# Building and testing:

There are a few options in the challenge building process, depending on the needs of the challenge.

## the default case

Normally, when a challenge is built, its `./$MODULE_ID/$CHALLENGE_ID/challenge` is just deployed into /challenge in the default docker container (simple `ubuntu:24.04` with some preinstalled packages and `exec-suid` for SUIDing interpreted programs.
At the end of the container built process, if a `./$MODULE_ID/$CHALLENGE_ID/.setup` file exists, it will be executed in the docker build context.
When the container is launched for a user to attempt the challenge, if a `./$MODULE_ID/$CHALLENGE_ID/.init` file exists (built as `/challenge/.init` in the resulting challenge image), it will be executed before as the challenge container starts up.

## tests

Tests are copied into a temporary directory in a running challenge container and executed with the `FLAG` variable set to the value of the random flag generated to `/flag`.

## custom environments

If a challenge needs build customization beyond `.setup`, it can specify its own `./$MODULE_ID/$CHALLENGE_ID/challenge/Dockerfile`, which will be used instead of the default dockerfile.

## templating

Any file that ends in `.j2` is automatically jinja2-formatted during challenge building.
Templates are passed in a seeded `random` for repeatable use at template time (e.g., `{{random.randrange()}}`).
Examples abound around the repository.

Template variables in output strings need double braces: `{{variable}}`.
This can be confusing in python code, because python f-strings use single braces (`{variable}`), so keep that in mind.

### inheriting templates

There are base templates sprinkled around this repository in `base_templates` subdirectories.
These templates typically `{% block %}` areas that you can override in your child template.
Use `{% extends %}` to extend a base template and tweak these blocks, not `{% include %}`.

Most base templates included in this repository support various customizations via a `settings` namespace that can be customized by child templates in a `setup` block.
Set variables in `{% block setup %}` blocks and call `{{- super() -}}` to preserve parent initialization.

### Key Template Files

- `base_templates/flask.py.j2` - Base Flask application template
- `base_templates/random_names.j2` - Macro for generating random endpoints and parameter names
- `default-dockerfile.j2` - Default Docker container template

Anything can be templated, including `./$MODULE_ID/$CHALLENGE_ID/challenge/Dockerfile.j2` (for example, to extend the `default-dockerfile.j2` template with additional packages to install and so on).
Before extending the default template, consider if it would not be easier and more understandable to just make a full `Dockerfile`.

Permissions are preserved when rendering a template.
If you want something executable, make the template executable (`chmod +x *.j2`).

## actually building

The repository contains all you need to build these challenges.

### Prerequisites

Install required Python packages in a virtual environment:

```bash
pip install jinja2 black pyastyle pwntools
```

### Building and Testing

```bash
# build and test
./build.py --test web-security/path-traversal-1

# build without testing into a directory to look at
./build.py web-security/path-traversal-1 --output-dir /tmp/output

# if you want to see a single file (for easier debugging)
./build.py web-security/path-traversal-1/tests_public/test_normal.py.j2
```

## Important Notes / Common Gotchas

- All `.j2` template files that should produce executable output must be made executable first
- Python scripts needing SUID should use the shebang: `#!/usr/bin/exec-suid -- /usr/bin/python3 -I`
- Web services (if any) should run on `challenge.localhost` port 80 (tests are executed with `--add-host challenge.localhost:127.0.0.1` for proper networking)
- Not all challenges need templates - use them only when randomization or reuse is important.

# pwn.college DOJO integration

**FUTURE WORK.**
This repository will contain various yamls files for different dojos.
These dojos will specify modules to include.
Each module will have its own `module.yml`.

# Porting legacy templates

We are in the process of porting the pwnshop-based curriculum and the multi-repo based curriculum to this format.
The old model was: each dojo would be its own repository (e.g., intro-to-cybersecurity-dojo, program-security-dojo, systems-security-dojo, software-exploitation-dojo, etc) of `./$MODULE_ID/$CHALLENGE_ID` directories full of files to deploy into `/challenge`.
Sometimes, these files were separately generated via pwnshop from the pwncollege-challenges repository, which has `./pwncollege_modules/$SLIGHTLY_DIFFERENT_MODULE_ID/__init__.py` files specifying challenge and verification logic.
These `__init__.py` files also specify jinja2 templates, sprinkled around the pwncollege-challenges and pwnshop repositories.
The dojo repositories' `module.yml` files would sometimes specify the pwnshop details for challenges.

The process of porting is:

1. Identify the challenges to be ported by reading the `module.yml` file of the emodule. If you are an AI, make this your TODO list: for each challenge, you will port out the challenge itself, the `tests_public` functionality tests (that don't give away the solution), and the `tests_private` solution/vulnerability tests. List each challenge and each challenge subtask in the todo list.
2. Determine any connections to the pwnshop templates by looking at `module.yml`. This will be specified by the `auxiliary: pwnshop:` dictionary, which will determine the pwnshop challenge class and other arguments.
3. If a pwnshop challenge is specified, look at `pwncollege-modules/$WHATEVER_MODULE_ID/__init__.py` for the appropriate class and determine the template and challenge logic to port out, if any.
4. Create base templates in `./$MODULE_ID/base_templates/` if multiple challenges share patterns
5. Port challenge files to `./$MODULE_ID/$CHALLENGE_ID/challenge/` (binaries, scripts, configs, etc.)
6. If using templates, use `{% extends %}` and `{% block setup %}` for customization
7. Ensure all executable files are marked as such: `chmod +x ./$MODULE_ID/$CHALLENGE_ID/**/*.j2`. Rendered files inherit permissions from the template.
8. Port verification logic to `./$MODULE_ID/$CHALLENGE_ID/tests_public` (functionality) and `./$MODULE_ID/$CHALLENGE_ID/tests_private` (exploitation)
9. Test thoroughly: `./build.py --test $MODULE_ID/$CHALLENGE_ID`
10. Once testcases pass, double-check the template (both rendered and at rest) against the legacy challenge to ensure that the challenge has been ported without any functionality change.


# In the meantime, some musings:

Some gaps we still need to fill:

- different architectures. Does docker cover all usecases?
- i have some doubts that this challenges-are-jinja-templates style will scale to all challenge complexities. yan85 has some hella spaghetti code. Maybe refactors will help, or maybe we'll need to have some other workarounds.
- should we follow symlinks during challege building? We do in the legacy case. Maybe only follow them if they point outside of the `challenge` dir? That might also be a PITA, though.
