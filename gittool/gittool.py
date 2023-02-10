#!/usr/bin/env python3
# -*- coding: utf8 -*-
# tab-width:4
from __future__ import annotations

import os
from pathlib import Path
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal

import click
import sh
from asserttool import ic
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from dulwich.repo import Repo
from mptool import output
from unmp import unmp
from walkup_until_found import walkup_until_found
from with_chdir import chdir

# from dulwich import porcelain

sh.mv = None  # use sh.busybox('mv'), coreutils ignores stdin read errors

signal(SIGPIPE, SIG_DFL)


def find_repo_root(
    path: Path,
    verbose: bool | int | float = False,
):
    ic(path)
    repo_root = walkup_until_found(path=path, name=".git", verbose=verbose).parent
    return repo_root


def timestamp_for_commit(commit):
    _tsc = sh.Command("git")
    _tsc = _tsc.bake("log")
    _tsc = _tsc.bake("-1", commit, "--pretty=format:%ct")
    _ts = int(str(_tsc(_tty_out=False)).strip())
    return _ts


def seconds_between_commits(commit1: str, commit2: str):
    _ts1 = timestamp_for_commit(commit1)
    _ts2 = timestamp_for_commit(commit2)
    _sec = abs(_ts2 - _ts1)
    return _sec


def unstaged_commits_exist(
    path: Path,
    verbose: bool | int | float = False,
) -> bool:
    # there is likely a angryfiles bug here...
    # result = git("diff-index", "HEAD", "--")
    repo_root = find_repo_root(path=path, verbose=verbose)
    if verbose:
        ic(path, repo_root)
    with chdir(repo_root, verbose=verbose):
        git_command = sh.Command("git")
        # git_command.bake('diff-index', "HEAD", "--")
        git_command = git_command.bake("diff-index", "HEAD")
        if verbose:
            ic(git_command)
        results = git_command(_tty_out=False).stdout.decode("utf8").splitlines()
        # ic(result.stdout)
        if verbose:
            ic(results)
        relative_path = path.relative_to(repo_root)
        # ic(relative_path)
        for result in results:
            if verbose:
                ic(result)
            if result.endswith(relative_path.as_posix()):
                return True
        # if path.as_posix() in result:
        #    return True
    return False

    # _git = sh.Command("/home/cfg/git/unstaged_changes_exist_for_file.sh")
    # try:
    #    _git(path.as_posix())
    # except sh.ErrorReturnCode_1 as e:
    #    ic(e)
    #    return True
    # return False


def get_remotes(
    repo_path: Path,
    verbose: bool | int | float = False,
) -> list[dict]:
    repo = Repo(repo_path)
    remotes = []
    for config_file in repo.get_config_stack().backends:
        for k, v in config_file.items():
            if verbose:
                print(f"{k=}", f"{v=}")
            if k[0] == b"remote":
                remotes.append({k[1].decode("utf8"): v[b"url"].decode("utf8")})
    return remotes


def commits_between_inclusive(
    commit1: str,
    commit2: str,
    *,
    verbose: bool | int | float = False,
):
    assert commit1 != commit2
    assert len(commit1) == len(commit2)
    _rev_list_command = sh.Command("git")
    _rev_list_command = _rev_list_command.bake("rev-list")
    _rev_list_command = _rev_list_command.bake("--count", f"{commit1}..{commit2}")
    _commit_count = abs(int(str(_rev_list_command(_tty_out=False)).strip())) + 1

    # commit_count = str(sh.git.rev-list("--count", "f{commit1}..{commit2}")).strip()
    if verbose:
        ic(_commit_count)
    return _commit_count


@click.group(no_args_is_help=True, cls=AHGroup)
@click_add_options(click_global_options)
@click.pass_context
def cli(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
):
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )


@cli.command("list-paths")
@click.argument("repo_paths", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def list_paths(
    ctx,
    repo_paths: tuple[str],
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
) -> None:
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    if repo_paths:
        iterator = repo_paths
    else:
        iterator = unmp(
            valid_types=[
                bytes,
            ],
            verbose=verbose,
        )
    del repo_paths

    index = 0
    for index, _path in enumerate(iterator):
        repo_path = Path(os.fsdecode(_path)).resolve()
        repo = Repo(repo_path)

        for thing in repo.open_index():
            repo_file_path = repo_path / Path(os.fsdecode(thing))
            if verbose:
                ic(index, repo_path, repo_file_path)
            # assert _path.exists()  # nope, use .lstat()
            output(
                os.fsencode(repo_file_path.as_posix()),
                dict_output=dict_output,
                reason=thing,
                tty=tty,
                verbose=verbose,
            )


@cli.command("list-remotes")
@click.argument("repo_paths", type=str, nargs=-1)
@click_add_options(click_global_options)
@click.pass_context
def list_remotes(
    ctx,
    repo_paths: tuple[str],
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
):
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    if repo_paths:
        iterator = repo_paths
    else:
        iterator = unmp(
            valid_types=[
                bytes,
            ],
            verbose=verbose,
        )
    del repo_paths

    index = 0
    for index, _path in enumerate(iterator):
        repo_path = Path(os.fsdecode(_path)).resolve()
        remotes = get_remotes(
            repo_path=repo_path,
            verbose=verbose,
        )
        for remote in remotes:
            output(
                remote, reason=None, dict_output=dict_output, tty=tty, verbose=verbose
            )


@cli.command("unstaged-commit")
@click.argument("path", type=str, nargs=1)
@click_add_options(click_global_options)
@click.pass_context
def unstaged_commit(
    ctx,
    path: str,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
):
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    _path = Path(path).resolve()
    result = unstaged_commits_exist(path=_path, verbose=verbose)
    output(
        result,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )


@cli.command()
@click.argument("commit1", type=str, nargs=1)
@click.argument("commit2", type=str, nargs=1)
@click_add_options(click_global_options)
@click.pass_context
def count_commits(
    ctx,
    commit1: str,
    commit2: str,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
):
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    _count = commits_between_inclusive(commit1, commit2, verbose=verbose)

    output(
        _count,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )


@cli.command("seconds-between-commits")
@click.argument("commit1", type=str, nargs=1)
@click.argument("commit2", type=str, nargs=1)
@click_add_options(click_global_options)
@click.pass_context
def _seconds_between_commits(
    ctx,
    commit1: str,
    commit2: str,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
):
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    _count = seconds_between_commits(commit1, commit2)

    output(
        _count,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )


@cli.command("head")
@click_add_options(click_global_options)
@click.pass_context
def _head(
    ctx,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool | int | float = False,
):
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    _rev_parse = sh.Command("git")
    _rev_parse = _rev_parse.bake("rev-parse", "HEAD")
    _rev_parse = str(_rev_parse(_tty_out=False)).strip()

    output(
        _rev_parse,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )
