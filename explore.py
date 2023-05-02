#!/usr/local/opt/python@3.8/bin/python3.8
import os
import sys
import re
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

global explore_result_text

click_log.basic_config()

CONTEXT_SETTINGS = dict(auto_envvar_prefix='HOMEASSISTANT')
_LOGGER = logging.getLogger(__name__)

pass_context = click.make_pass_decorator(  # pylint: disable=invalid-name
    Configuration, ensure=True
)


def lib():
    return """

global get
get = lambda  d, e : d[e] if str(type(d)) in ("<class 'dict'>") else d.as_dict()[e] if 'as_dict' in dir(d) else getattr(d,e)

def explore( name, path ):
    import json
    global explore_result_text


    explore_result_text = ""
    try:
        printables = ["<class '" + n + "'>" for n in ("str","bool","int","dict","set","dict_items")]
        def fmt(s):
            s=str(s)
            if len(s) > 210:
                return(s[:200] + "...")
            return(s)
        t = str(type(path))
        if t == "<class 'dict'>":
            d = [ (e, str(type(path.get(e))), fmt( path.get(e) ) if str(type(path.get(e))) in printables else "" ) for e in path.keys() ]
        elif t in printables:
            d = [ [ name,eval('str(type("'+name+'"))'),str(path) ] ]
        elif t in ("<class 'list'>","<class 'set'>","<class 'itertools.chain'>"):
            path=list(path)
            d = [ ('['+str(e)+']', str(type(path[e])), fmt( path[e] ) if str(type(path[e])) in printables else "" ) for e in range(len(path)) ]
        else:
            d = [ (e, str(type(getattr(path,e))), fmt( getattr(path,e) ) if str(type(getattr(path,e))) in printables else "" ) for e in dir(path) if not str(e).startswith('_') and str(e) != 'attribute_value' ]
        explore_result_text = json.dumps({ 'type' : t, 'dir': d })
    except Exception as ex:  # pylint: disable=broad-except
        explore_result_text = json.dumps({ 'exception' : str(ex) })
    return explore_result_text[:2550]

def more(offset):
    global explore_result_text
    return explore_result_text[offset:offset+2550]
"""
def getwidths( a ):
    w=[0,0,0]
    for e in a:
       for i in range(3):
           if len(str(e[i])) > w[i]: w[i] = len(str(e[i]))
    w[2] = 190 - w[1] - w[0]
    if w[2] < 50: w[2] = 50
    return w

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
@click.argument('path', required=False)

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
@click.option(
    '--interactive',
    '-i',
    is_flag=True,
    default=False,
    help=(
        'Interactive.'
        ' Continue in interactive mode after output of initial path on command-line.'
    ),
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    default=False,
    help=(
        'Verbose.'
        ' Give verbose output.'
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
    path: Optional[str],
    interactive: bool,
    verbose: bool,
) -> None:
    """Explore for Home Assistant."""
    ctx.server = server
    ctx.token = token
    ctx.password = password
    ctx.timeout = timeout
    ctx.insecure = insecure
    ctx.cert = cert
    ctx.path = path
    ctx.interactive = True if not path else interactive
    ctx.verbose = True if not path else interactive

    if path:
        parts = re.split(r'(\[|\.|\?)', path)
        path = []
        p = [ parts[0] ] + [ e[1:] if e[0] == '.' else e for e in ["".join(parts[i:i+2]) for i in range(1, len(parts), 2)] ]
        for i in range(len(p)):
            path.append( {'n' : p[i], 't': "<class 'homeassistant.core.HomeAssistant'>" } )
            if i > 0:
                if p[i].startswith('['):
                    path[i-1]['t'] = "<class 'list'>"
                elif p[i].startswith('?'):
                    path[i-1]['t'] = "<class 'list'>"
                    path[i]['t'] = "<class 'list'>"
                elif p[i].startswith('get('):
                    path[i]['n'] = p[i][5:-2]
                    path[i-1]['t'] = "<class 'dict'>"
                else:
                    path[i-1]['t'] = "class"
    else:
        path = [ { 'n':'hass', 't':"<class 'homeassistant.core.HomeAssistant'>" } ]

    while True:
        if verbose: print(repr(path))
        prior=""
        filters = [""]
        filter_num = 0
        prompt=""

        i = 0
        for e in path:
            if e['n'].startswith('?'):
                filters[ filter_num ] = "list( filter( " + e['n'][1:].replace('%5b','[').replace('%5d',']').replace('%2e','.') + "," + filters[ filter_num - 1 ] + ") )"
                prompt += e['n']
            elif e['n'].startswith('['):
                filters[ filter_num ] = 'list(' + filters[ filter_num ] + ')'
                if e['n'] == '[*]':
                    if i == len(path) - 1:
                        filters[ filter_num ] += '[0]'
                    else:
                        filter_num += 1
                        filters.append("")
                else:
                    filters[ filter_num ] += e['n']
                prompt += e['n']
            elif prior == "":
                filters[ filter_num ] += e['n']
                prompt += e['n']
            elif prior == "<class 'dict'>":
                filters[ filter_num ] += ".get('" + e['n'] + "')"
                prompt += ".get('" + e['n'] + "')"
            else:
                filters[ filter_num ] += "." + e['n']
                prompt += "." + e['n']
            prior = e['t']
            i += 1

        if filter_num > 0:
            p = '[ e ' + filters[1] + ' for e in ' + filters[0] + ']'
        else:
            p = filters[ 0 ]

        if verbose:
            print("send ----> " + p )
            print("prompt ----> " + prompt )
        api.call_service(ctx,'ha_introspection','do_introspection',{'statement':lib(), 'expression':'explore("'+prompt+'",' + p + ')'})
        part = api.render_template(ctx, "|{% for i in range(1+states.introspection.len.state|int) %}{{ states.introspection['result_' ~ i]['state'] }}{% endfor %}", {})[1:]
        output = ""
        while part != '' and part != '<none>':
            output += part
            if output == '' or output[0] != '{': break
            api.call_service(ctx,'ha_introspection','do_introspection',{'statement':lib(), 'expression':'more(' + str(len(output)) + ')'})
            part = api.render_template(ctx, "|{% for i in range(1+states.introspection.len.state|int) %}{{ states.introspection['result_' ~ i]['state'] }}{% endfor %}", {})[1:]

        map = {}
        if output.startswith("{"):
            resp = json.loads(output)
            if ctx.interactive: print("")
            if 'exception' in resp:
                print('Exception: ' + resp['exception'])
            else:
                print(prompt + " " + resp[ 'type' ])
                (w0,w1,w2) = getwidths( resp['dir'] )
                for d in resp['dir']:
                    d2 = d[2][:w2] + "..." if len(d[2]) > w2 - 5 else d[2]
                    print(f"     {str(d[0]):<{w0}} {str(d[1]):<{w1}} {str(d2):<{w2}}")
                    map[ str(d[0]) ] = d[1]
        else:
            print("<-----" + output)
        if not ctx.interactive: break
        s=""
        while True:
            s = input(prompt + '> ')
            if s == '':
                pass
            elif s == '.':
                break
            elif s == '..':
                if len(path) > 1: 
                    path = path [:-1]
                else:
                    path=[ { 'n' : 'hass', 't': "<class 'homeassistant.core.HomeAssistant'>" } ]
                break
            elif s[0] == '?':
                path.append( {'n': s, 't': 'class'} )
                break
            elif s[0] == '[':
                path.append( {'n': s, 't': 'class'} )
                break
            elif s == 'globals()':
                path=[ { 'n' : s, 't': "<class 'dict'>" } ]
                break
            elif s in map:
                path.append( { 'n' : s, 't': map[s] } )
                break
            elif s.replace('()','') in map:
                path.append( { 'n' : s, 't': map[s.replace('()','')] } )
                break
            else:
                print("Not found")
        # print( path )

if __name__ == '__main__':
    run()
