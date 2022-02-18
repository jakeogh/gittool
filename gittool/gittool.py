#!/usr/bin/env python3
# -*- coding: utf8 -*-
# tab-width:4

import os
import sys
from pathlib import Path
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal
from typing import Union

import click
import sh
from asserttool import ic
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
#from dulwich import porcelain
from dulwich.repo import Repo
from mptool import output
from unmp import unmp

sh.mv = None  # use sh.busybox('mv'), coreutils ignores stdin read errors

signal(SIGPIPE, SIG_DFL)


def unstaged_commits_exist(path: Path) -> bool:
    _git = sh.Command("/home/cfg/git/unstaged_changes_exist_for_file.sh")
    try:
        _git(path.as_posix())
    except sh.ErrorReturnCode_1:
        return True
    return False


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


@cli.command('list-paths')
@click.argument("paths", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def list_paths(ctx,
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
    for index, _path in enumerate(iterator):
        repo_path = Path(os.fsdecode(_path))
        repo = Repo(repo_path)

        for thing in repo.open_index():
            repo_file_path = repo_path / Path(os.fsdecode(thing))
            if verbose:
                ic(index, repo_path, repo_file_path)
            #assert _path.exists()  # nope, use .lstat()
            output(os.fsencode(repo_file_path.as_posix()), tty=tty, verbose=verbose,)



