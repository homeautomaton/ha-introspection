#!/usr/local/opt/python@3.8/bin/python3.8
import os
import sys
import logging
from typing import List, Optional, Union, cast

import json

import click
from click.core import Command, Context, Group
import click_log

import homeassistant_cli.autocompletion as autocompletion
from homeassistant_cli.config import Configuration
import homeassistant_cli.const as const
from homeassistant_cli.helper import debug_requests_on, to_tuples
import homeassistant_cli.remote as api

click_log.basic_config()

CONTEXT_SETTINGS = dict(auto_envvar_prefix='HOMEASSISTANT')
_LOGGER = logging.getLogger(__name__)

pass_context = click.make_pass_decorator(  # pylint: disable=invalid-name
    Configuration, ensure=True
)


def lib():
     return """
def no_(a):
    return [ e for e in a if not e.startswith('_') ]

def head(a,cnt=20):
    return a[:cnt]

def fmt(a):
    result=''
    for n in a:
        result += str(n) + '\\n'
    return result

def explore(path):
    import json
    t = str(type(path))
    if t == "<class 'dict'>":
        d = [ (e,str(type(path.get(e)))) for e in path.keys() ]
    else:
        d = [ (e,str(type(getattr(path,e)))) for e in dir(path) if not str(e).startswith('_') ]
    result = json.dumps({ 'type' : t, 'dir': d })
    with open("/tmp/explore.txt", "w") as file:
        file.write(result) 

    return result[:2550]

def more(offset):
    with open("/tmp/explore.txt", "r") as file:
        result = file.read()
    return result[offset:offset+2550]
"""

def run() -> None:
    """Run entry point.

    Wraps click for full control over exception handling in Click.
    """

    try:
        # Could use cli.invoke here to use the just created context
        # but then shell completion will not work. Thus calling
        # standalone mode to keep that working.
        result = cli.main(standalone_mode=False)
        if isinstance(result, int):
            sys.exit(result)

    # Exception handling below is done to use logger
    # and mimick as close as possible what click would
    # do normally in its main()
    except click.ClickException as ex:
        ex.show()  # let Click handle its own errors
        sys.exit(ex.exit_code)
    except click.Abort:
        _LOGGER.critical("Aborted!")
        sys.exit(1)
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.error("%s: %s", type(ex).__name__, ex)
        sys.exit(1)


def _default_token() -> Optional[str]:
    """Handle the token provided as env variable."""
    return os.environ.get('HASS_TOKEN', os.environ.get('HASSIO_TOKEN', None))

@click.command(context_settings=CONTEXT_SETTINGS)

@click.option(
    '--server',
    '-s',
    help=(
        'The server URL or `auto` for automatic detection. Can also be set '
        'with the environment variable HASS_SERVER.'
    ),
    default="auto",
    show_default=True,
    envvar='HASS_SERVER',
)
@click.option(
    '--token',
    default=_default_token,
    help=(
        'The Bearer token for Home Assistant instance. Can also be set with '
        'the environment variable HASS_TOKEN.'
    ),
    envvar='HASS_TOKEN',
)
@click.option(
    '--password',
    default=None,
    help=(
        'The API password for Home Assistant instance. Can also be set with '
        'the environment variable HASS_PASSWORD.'
    ),
    envvar='HASS_PASSWORD',
)
@click.option(
    '--timeout',
    help='Timeout for network operations.',
    default=const.DEFAULT_TIMEOUT,
    show_default=True,
)

@click.option(
    '--cert',
    default=None,
    envvar="HASS_CERT",
    help="Path to client certificate file (.pem) to use when connecting.",
)
@click.option(
    '--insecure',
    is_flag=True,
    default=False,
    help=(
        'Ignore SSL Certificates.'
        ' Allow to connect to servers with self-signed certificates.'
        ' Be careful!'
    ),
)


@pass_context
def cli(
    ctx: Configuration,
    server: str,
    token: Optional[str],
    password: Optional[str],
    timeout: int,
    insecure: bool,
    cert: str,
) -> None:
    """Explore for Home Assistant."""
    ctx.server = server
    ctx.token = token
    ctx.password = password
    ctx.timeout = timeout
    ctx.insecure = insecure
    ctx.cert = cert

    path = [ { 'n':'hass', 't':'class' } ]
    while True:
        prior=""
        p=""
        for e in path:
            if prior == "":
                p += e['n']
            elif prior == "<class 'dict'>":
                p += ".get('" + e['n'] + "')"
            else:
                p += "." + e['n'] + ""
            prior = e['t']
        print(p)

        api.call_service(ctx,'ha_introspection','do_introspection',{'statement':lib(), 'expression':'explore(' + p + ')'})
        part = api.render_template(ctx, "|{% for i in range(1+states.introspection.len.state|int) %}{{ states.introspection['result_' ~ i]['state'] }}{% endfor %}", {})[1:]
        output = ""
        x = ""
        while part != '' and part != '<none>':
            output += part
            x += part + "\n\n"
            api.call_service(ctx,'ha_introspection','do_introspection',{'statement':lib(), 'expression':'more(' + str(len(output)) + ')'})
            part = api.render_template(ctx, "|{% for i in range(1+states.introspection.len.state|int) %}{{ states.introspection['result_' ~ i]['state'] }}{% endfor %}", {})[1:]

        print(x)
        map = {}
        if output.startswith("{"):
            resp = json.loads(output)
            print("")
            print(p + " " + resp[ 'type' ])
            for d in resp['dir']:
                print( "    " + str(d) )
                map[ d[0] ] = d[1]
        else:
            print(output)
        s = input(p+'> ')
        if s == '..':
            if len(path) > 1: 
                path = path [:-1]
        elif s in map:
            path.append( { 'n' : s, 't': map[s] } )
        else:
            print("Not found")

if __name__ == '__main__':
    run()
