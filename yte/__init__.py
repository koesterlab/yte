import sys
import yaml
import plac
from yte.context import Context
from yte.process import FEATURES, _process_yaml_value
from yte.document import Document


def process_yaml(
    file_or_str,
    outfile=None,
    variables=None,
    require_use_yte=False,
    disable_features=None,
):
    """Process a YAML file or string with YTE,
    returning the processed version.

    # Arguments
    * file_or_str - file object or string to render
    * outfile - output file to write to, if None output is returned as string
    * variables - dict of variables (must have valid python names) to be available in
      the template
    * require_use_yte - skip templating if there is no `__use_yte__ = True`
      statement in the top level of the document
    * disable_features - list of features that should be disabled during rendering.
      Possible values to choose from are ["definitions", "variables"]
    """
    if variables is None:
        variables = dict()
    variables["_process_yaml_value"] = _process_yaml_value
    doc = Document()
    variables["doc"] = doc
    variables["this"] = doc

    try:
        yaml_doc = yaml.load(file_or_str, Loader=yaml.FullLoader)
    except yaml.scanner.ScannerError as e:
        raise yaml.scanner.ScannerError(
            f"{e}\nNote that certain characters like colons have a special "
            "meaning in YAML and hence keys or values containing them have "
            "to be quoted."
        )

    is_use_yte = yaml_doc.get("__use_yte__") if isinstance(yaml_doc, dict) else None
    if is_use_yte is not None:
        # remove __use_yte__ key
        yaml_doc.pop("__use_yte__")

    if not require_use_yte or is_use_yte:
        if disable_features is not None:

            disable_features = frozenset(disable_features)
            if not FEATURES.issuperset(disable_features):
                raise ValueError("Invalid features given to `disable_features`.")
        else:
            disable_features = frozenset([])

        result = _process_yaml_value(
            yaml_doc,
            variables,
            context=Context(),
            disable_features=disable_features,
        )
    else:
        # do not process document since use_yte is required but not found in document
        result = yaml_doc

    if outfile is not None:
        yaml.dump(result, outfile, sort_keys=False)
    else:
        return result


@plac.flg(
    "require_use_yte",
    "Require that the document contains a `__use_yte__: true` statement at the top level. "
    "If the statement is not present or false, return document unprocessed "
    "(except removing the `__use_yte__: false` statement if present)",
)
@plac.opt(
    "variables",
    "Path to YAML file with definitions that will be available as Python variables "
    "when rendering the template Must have a map with keys at the top level, not a list. "
    "The file can be a YTE template itself (e.g. to build it dynamically from env vars).",
)
def cli(
    require_use_yte=False,
    variables=None,
):
    """Process a YAML file given at STDIN with YTE,
    and print the result to STDOUT.

    Note: if nothing is provided at STDIN,
    this will wait forever.
    """
    if variables is not None:
        with open(variables, "r") as infile:
            variables = process_yaml(infile, require_use_yte=require_use_yte)
            if not isinstance(variables, dict):
                raise ValueError(
                    "Given variables file has to contain a map with keys at the top-level."
                )

    process_yaml(
        sys.stdin,
        outfile=sys.stdout,
        require_use_yte=require_use_yte,
        variables=variables,
    )


def main():
    plac.call(cli)
