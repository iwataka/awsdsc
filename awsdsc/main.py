"""Provides main features for CLI"""

import json
import re
import sys
from datetime import date, datetime
from typing import Iterator, Union

import boto3.session
import click
import yaml
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import (
    Completer,
    FuzzyCompleter,
    FuzzyWordCompleter,
    NestedCompleter,
)
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer, YamlLexer

from awsdsc import __version__
from awsdsc.exception import AwsdscException, UnsupportedTypeException
from awsdsc.processor import ResourceTypeProcessor


def generate_processors(
    session: boto3.session.Session,
    cls=ResourceTypeProcessor,
) -> Iterator[ResourceTypeProcessor]:
    subclasses = cls.__subclasses__()
    if len(subclasses) == 0:
        yield cls(session)
    for c in subclasses:
        for p in generate_processors(session, c):
            yield p


def get_processor(
    typ: str,
    processors: list[ResourceTypeProcessor],
) -> ResourceTypeProcessor:
    try:
        return next(p for p in processors if typ in p.list_types())
    except StopIteration:
        raise UnsupportedTypeException(typ)


def describe(
    typ: str,
    key_values: dict[str, str],
    processors: list[ResourceTypeProcessor],
) -> Union[list[dict], dict]:
    return get_processor(typ, processors).describe(key_values)


def list_candidates(
    typ: str,
    processors: list[ResourceTypeProcessor],
) -> list[dict]:
    return get_processor(typ, processors).list_candidates(typ)


def list_types(processors: list[ResourceTypeProcessor]) -> list[str]:
    return list(set(sum([p.list_types() for p in processors], [])))


def print_result(
    result: Union[dict, list[dict]],
    style: str,
    colorize: bool,
):
    if style == "yaml":
        txt = yaml.dump(result)
        lexer = YamlLexer()
    elif style == "json":
        txt = json.dumps(result, indent=2, default=json_serialize)
        lexer = JsonLexer()
    else:
        raise Exception(f"Unknown stye: {style}")

    if colorize:
        txt = highlight(txt, lexer, TerminalFormatter())

    print(txt)


def json_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def describe_and_print_result(
    key_values: dict[str, str],
    fmt: str,
    typ: str,
    colorize: bool,
    processors: list[ResourceTypeProcessor],
):
    result = describe(typ, key_values, processors)
    if isinstance(result, list) and len(result) == 1:
        result = result[0]
    print_result(result, fmt, colorize)


class ResourceTypeValidator(Validator):
    def __init__(self):
        self.input_pattern = re.compile(r"^\s*AWS::[^\s:]+::[^\s:]+\s*$")

    def validate(self, document):
        if not self.input_pattern.match(document.text):
            raise ValidationError(message="Invalid AWS resource name pattern")


class QueryRecognizer:
    def __init__(self):
        self.operator = "="
        self.separator = ","
        self.query_pattern = re.compile(
            fr"^\s*([^\s{self.operator}]+)\s*{self.operator}\s*([^\s{self.operator}]+)\s*$"
        )

    def to_text(self, key_values: dict[str, str]) -> str:
        return self.separator.join(
            [f"{k} {self.operator} {v}" for k, v in key_values.items()]
        )

    def to_key_values(self, text: str) -> dict[str, str]:
        result = {}
        for q in text.split(self.separator):
            m = self.query_pattern.match(q)
            if m is None:
                raise Exception(f"{q} doesn't match to query pattern.")
            k, v = m.groups()
            result[k] = v
        return result


class ResourceQueryValidator(Validator):
    def __init__(
        self,
        keys: list[str],
        query_recognizer: QueryRecognizer,
        placeholder_key_limit: int = 10,
    ):
        self.keys = keys
        self.query_recognizer = query_recognizer
        self.placeholder_key_limit = placeholder_key_limit
        op = query_recognizer.operator
        self.query_pattern = re.compile(
            fr"^\s*({'|'.join(keys)})\s*{op}\s*([^\s{op}]+)\s*$"
        )

    def validate(self, document):
        for t in document.text.split(self.query_recognizer.separator):
            if not self.query_pattern.match(t):
                raise ValidationError(message="Invalid resource query pattern")

    def generate_placeholder(self):
        key_pattern = "|".join(self.keys[: self.placeholder_key_limit])
        if len(self.keys) > self.placeholder_key_limit:
            key_pattern += "|..."
        return f"key({key_pattern}) = value, ..."


def run_show_supported_types(processors: list[ResourceTypeProcessor]):
    types = list_types(processors)
    for t in sorted(types):
        print(t)


def cands_to_nested_dict(cands):
    result = {}
    for c in cands:
        for k, v in c.items():
            if v:
                if k in result:
                    result[k]["="][v] = None
                else:
                    result[k] = {"=": {v: None}}
    return result


class QueryCompleter(Completer):
    def __init__(self, base_completer, query_recognizer: QueryRecognizer):
        self.base_completer = base_completer
        self.query_recognizer = query_recognizer

    def get_completions(self, document, complete_event):
        curpos = document.cursor_position
        start = document.text[:curpos].rfind(self.query_recognizer.separator) + 1
        end = document.text[curpos:].find(self.query_recognizer.separator)
        if end >= 0:
            d = Document(document.text[start:end], cursor_position=curpos - start)
        else:
            d = Document(document.text[start:], cursor_position=curpos - start)
        return self.base_completer.get_completions(d, complete_event)


def run_default(
    typ: str,
    query: str,
    fmt: str,
    colorize: bool,
    processors: list[ResourceTypeProcessor],
):
    try:
        session: PromptSession = PromptSession(
            complete_while_typing=True,
            complete_in_thread=True,
            validate_while_typing=True,
            bottom_toolbar="[Tab] autocompletion",
        )

        typ = typ or session.prompt(
            message="Resource type> ",
            completer=FuzzyWordCompleter(list_types(processors)),
            validator=ResourceTypeValidator(),
            placeholder="AWS::SERVICE::DATA_TYPE",
        )

        query_recognizer = QueryRecognizer()
        query = query or inquire_query(session, typ, query_recognizer, processors)
    except KeyboardInterrupt:
        raise AwsdscException("Quit by user input")

    key_values = query_recognizer.to_key_values(query)
    describe_and_print_result(key_values, fmt, typ, colorize, processors)


def inquire_query(
    session: PromptSession,
    typ: str,
    query_recognizer: QueryRecognizer,
    processors: list[ResourceTypeProcessor],
) -> str:
    candidates = list_candidates(typ, processors)
    if not candidates:
        raise AwsdscException(f"No {typ} resources found")
    nested_dict = cands_to_nested_dict(candidates)

    query_validator = ResourceQueryValidator(
        list(nested_dict.keys()),
        query_recognizer,
    )

    return session.prompt(
        message="Query> ",
        completer=FuzzyCompleter(
            QueryCompleter(
                NestedCompleter.from_nested_dict(nested_dict),
                query_recognizer,
            )
        ),
        validator=query_validator,
        placeholder=query_validator.generate_placeholder(),
    )


@click.command()
@click.option(
    "--type",
    "-t",
    help="aws resource type to describe",
    metavar="TYPE",
)
@click.option(
    "--query",
    "-q",
    help="query for searching target aws resource",
    metavar="QUERY",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"], case_sensitive=True),
    help="output style. YAML and JSON are available.",
    default="json",
    show_default=True,
    envvar="AWSDSC_FORMAT",
    show_envvar=True,
)
@click.option(
    "--colorize/--no-colorize",
    "-c",
    help="colorize describe output",
    default=False,
    show_default=True,
    envvar="AWSDSC_COLORIZE",
    show_envvar=True,
)
@click.option(
    "--show-supported-types",
    is_flag=True,
    help="show AWS resource types supported by this command",
    default=False,
)
@click.option(
    "--profile",
    help="AWS profile to use in this command",
    metavar="PROFILE",
)
@click.option(
    "--region",
    help="AWS region to use in this command",
    metavar="REGION",
)
@click.version_option(version=__version__)
def cli(
    type: str,
    query: str,
    format: str,
    colorize: bool,
    show_supported_types: bool,
    profile: str,
    region: str,
):
    """Universal describe command for AWS resources"""
    try:
        session_params = {}
        if profile:
            session_params["profile_name"] = profile
        if region:
            session_params["region_name"] = region
        session = boto3.session.Session(**session_params)
        processors = list(sorted(generate_processors(session)))

        if show_supported_types:
            run_show_supported_types(processors)
            sys.exit(0)

        run_default(type, query, format, colorize, processors)

    except AwsdscException as e:
        print_formatted_text(HTML(f"<ansired>{str(e)}</ansired>"))
        sys.exit(1)


def main():
    cli()


if __name__ == "__main__":
    main()
