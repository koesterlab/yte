# YTE - A YAML template engine with Python expressions

[![Docs](https://img.shields.io/badge/user-documentation-green)](https://yte-template-engine.github.io)
[![test coverage: 100%](https://img.shields.io/badge/test%20coverage-100%25-green)](https://github.com/yte-template-engine/yte/blob/main/pyproject.toml#L30)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/yte-template-engine/yte/CI)
![PyPI](https://img.shields.io/pypi/v/yte)
[![Conda Recipe](https://img.shields.io/badge/recipe-yte-green.svg)](https://anaconda.org/conda-forge/yte)
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/yte.svg)](https://anaconda.org/conda-forge/yte)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/yte.svg)](https://github.com/conda-forge/yte-feedstock)


YTE is a template engine for YAML format that utilizes the YAML structure in combination with Python expressions for enabling to dynamically build YAML documents.

## Syntax

The key idea of YTE is to rely on the YAML structure to enable conditionals, loops and other arbitrary Python expressions to dynamically render YAML files.
Python expressions are thereby declared by prepending them with a `?` anywhere in the YAML.
Any such value will be automatically evaluated by YTE, yielding plain YAML as a result.
Importantly, YTE templates are still valid YAML files (for YAML, the `?` expressions are just strings).

### Conditionals

<!-- template -->

```yaml
?if True:
  foo: 1
?elif False:
  bar: 2
?else:
  bar: 1
```

<!-- rendered -->

```yaml
foo: 1
```

<!-- template -->

```yaml
?if True:
  - a
  - b
```

<!-- rendered -->

```yaml
- a
- b
```

<!-- template -->

```yaml
- foo
- bar
- ?if True:
    baz
  ?else:
    bar
```

<!-- rendered -->


```yaml
- foo
- bar
- baz
```


### Loops

<!-- template -->

```yaml
?for i in range(2):
  '?f"key:{i}"': 1  # When expressions in keys or values contain colons, they need to be additionally quoted.
  ?if i == 1:
      foo: true
```

<!-- rendered -->

```yaml
"key:0": 1
"key:1": 1
foo: true
```

### Accessing already rendered document parts

A globally available object `this` (a wrapper around a Python dict)
enables to access parts of the document that have already been rendered above.
This way, one can often avoid variable definitions (see below).
In addition to normal dict access, the object allows to search (`this.dpath_search`) and access (`this.dpath_get`) its contents via [dpath](https://github.com/dpath-maintainers/dpath-python) queries (see the [dpath docs](https://github.com/dpath-maintainers/dpath-python) for allowed expressions).
Simple dpath get queries can also be performed by putting the dpath query directly into the square bracket operator of the `doc` object (the logic in that case is as follows: first, the given value is tried as plain key, if that fails, `this.dpath_get` is tried as a fallback); see example below.

<!-- template -->

```yaml
foo: 1
bar:
  a: 2
  # dict access
  b: ?this["foo"] + this["bar"]["a"]
  # implicit simple dpath get query
  c: ?this["bar/a"]
  # explicit dpath queries
  d: ?this.dpath_get("foo") + this.dpath_get("bar/a")
```

<!-- rendered -->

```yaml
foo: 1
bar:
  a: 2
  b: 3
  c: 2
  c: 3
```

### Variable definitions

The special keyword `__variables__` allows to define variables that can be reused below.
It can be used anywhere in the YAML, also repeatedly and inside of ifs or loops
with the restriction of not having duplicate `__variables__` keys on the same level.

The usage of `__variables__` can be disabled via the API.

<!-- template -->

```yaml
__variables__:
  first: foo
  second: 1.5
  # apart from constant values as defined above, also Python expressions are allowed:
  third: ?2 * 3 


a: ?first
b: ?second
c:
  ?for x in range(3):
    __variables__:
      y: ?x * 2
    ?if True:  
      - ?y
```

<!-- rendered -->

```yaml
a: foo
b: 1.5
c:
- 0
- 2
- 4
```

### Arbitrary definitions

The special keyword `__definitions__` allows to define custom statements.
It can be used anywhere in the YAML, also repeatedly and inside of ifs or loops
with the restriction of not having duplicate `__definitions__` keys on the same level.

The usage of `__definitions__` can be disabled via the API.

<!-- template -->

```yaml
  __definitions__:
    - from itertools import product
    - someval = 2
    - |
      def squared(value):
          return value ** 2

  ?for item in product([1, 2], ["a", "b"]):
    - ?f"{item}"

  ?if True:
    - ?squared(2) * someval
    - someval: ?someval
```

<!-- rendered -->

```yaml
- 1-a
- 1-b
- 2-a
- 2-b
- 4
- someval: 2
```

## Usage

### Installation

YTE can be installed as a Python package via [PyPi](https://pypi.org/project/yte) or [Conda/Mamba](https://anaconda.org/conda-forge/yte).

### Python API

Alternatively, you can invoke YTE via its Python API:

```python
from yte import process_yaml

# Set some variables as a Python dictionary.
variables = ...

# Render a string and obtain the result as a Python dict.
result = process_yaml("""
?for i in range(10):
  - ?f"item-{i}"
""", variables=variables)

# Render a file and obtain the result as a Python dict.
with open("the-template.yaml", "r") as template:
    result = process_yaml(template, variables=variables)

# Render a file and write the result as valid YAML.
with open("the-template.yaml", "r") as template, open("the-rendered-version.yaml", "w") as outfile:
    result = process_yaml(template, outfile=outfile, variables=variables)

# Render a file while disabling the __definitions__ feature.
with open("the-template.yaml", "r") as template:
    result = process_yaml(template, variables=variables, disable_features=["definitions"])

# Render a file while disabling the __variables__ feature.
with open("the-template.yaml", "r") as template:
    result = process_yaml(template, variables=variables, disable_features=["variables"])

# Render a file while disabling the __variables__ and __definitions__ feature.
with open("the-template.yaml", "r") as template:
    result = process_yaml(template, variables=variables, disable_features=["variables", "definitions"])

# Require that the document contains a `__use_yte__: true` statement at the top level.
# If the statement is not present or false, return document unprocessed (except removing the `__use_yte__: false` statement if present).
with open("the-template.yaml", "r") as template:
    result = process_yaml(template, variables=variables, require_use_yte=True)
```

### Command line interface

YTE also provides a command line interface:

```bash
yte --help
```

It can be used to process a YTE template from STDIN and prints the rendered version to STDOUT:

```bash
yte < template.yaml > rendered.yaml
```

In case your template requires additional variables to be available, you can pass them via another YAML file that has to contain a map of values at the top-level, e.g.

```bash
yte --variables myvars.yaml < template.yaml > rendered.yaml
```

Note that the variables file can itself be a template, so that it might contain dynamic content that is decided on based e.g. on environment variables or database access (since there can be any Python code in YTE templates).

## Comparison with other engines

Lots of template engines are available, for example the famous generic [jinja2](https://jinja.palletsprojects.com).
The reasons to generate a YAML specific engine are

1. The YAML syntax can be exploited to simplify template expression syntax, and make it feel less foreign (i.e. fewer special characters for control flow needed) while increasing human readability.
2. Whitespace handling (which is important with YAML since it has a semantic there) becomes unnecessary (e.g. with jinja2, some [tuning](https://radeksprta.eu/posts/control-whitespace-in-ansible-templates) is required to obtain proper YAML rendering).

Of course, YTE is not the first YAML specific template engine.
Others include

* [Yglu](https://yglu.io)
* [Emrichen](https://github.com/con2/emrichen)

The main difference between YTE and these two is that YTE extends YAML with plain Python syntax instead of introducing another specialized language.
Of course, the choice is also a matter of taste.
