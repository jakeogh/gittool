#!/usr/bin/env python3
# -*- coding: utf8 -*-
# tab-width:4

from pathlib import Path
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal
from typing import Union

import click
import sh
from asserttool import ic
from asserttool import tv
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from mptool import output
from unmp import unmp
from with_chdir import chdir

sh.mv = None  # use sh.busybox('mv'), coreutils ignores stdin read errors

signal(SIGPIPE, SIG_DFL)

#@with_plugins(iter_entry_points('click_command_tree'))
@click.group(no_args_is_help=True, cls=AHGroup)
@click_add_options(click_global_options)
@click.pass_context
def cli(ctx,
        verbose: Union[bool, int, float],
        verbose_inf: bool,
        ):

    tty, verbose = tv(ctx=ctx,
                      verbose=verbose,
                      verbose_inf=verbose_inf,
                      )


@cli.command()
@click.argument("paths", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def list_files(ctx,
               paths: tuple[str],
               verbose: Union[bool, int, float],
               verbose_inf: bool,
               ):

    tty, verbose = tv(ctx=ctx,
                      verbose=verbose,
                      verbose_inf=verbose_inf,
                      )

    if paths:
        iterator = paths
    else:
        iterator = unmp(valid_types=[bytes,], verbose=verbose)
    del paths

    index = 0
    for index, path in enumerate(iterator):
        ic(index, path)
        with chdir(path):
            git_command = sh.Command('git')
            git_command('ls-tree', '--full-tree', '-r', '--name-only', 'HEAD')
            _stderr = git_command.stderr
            _stdout = git_command.stdout
            ic(_stdout)
            ic(_stderr)

