from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex

import paramiko


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password")
    parser.add_argument("--key-file")
    parser.add_argument("--local-script", required=True)
    parser.add_argument("--remote-script", required=True)
    parser.add_argument("--remote-log")
    parser.add_argument("--before-command")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--remote-arg", action="append", default=[])
    return parser.parse_args()


def build_remote_command(args: argparse.Namespace) -> str:
    remote_script = shlex.quote(args.remote_script)
    remote_args = " ".join(shlex.quote(arg) for arg in args.remote_arg)
    script_command = f"bash {remote_script}"

    if remote_args:
        script_command = f"{script_command} {remote_args}"

    command_parts = [f"chmod +x {remote_script}"]
    if args.before_command:
        command_parts.append(args.before_command)

    if args.wait:
        command_parts.append(script_command)
    else:
        if not args.remote_log:
            raise ValueError("--remote-log is required unless --wait is set")

        remote_log = shlex.quote(args.remote_log)
        command_parts.append(
            f"nohup {script_command} > {remote_log} 2>&1 & echo $!"
        )

    return " && ".join(command_parts)


def main() -> None:
    args = parse_args()
    local_script = Path(args.local_script)
    if not local_script.exists():
        raise FileNotFoundError(f"Local script not found: {local_script}")

    script_text = local_script.read_text(encoding="utf-8")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_file = os.path.expanduser(args.key_file) if args.key_file else None
    client.connect(
        args.host,
        port=args.port,
        username=args.user,
        password=args.password,
        key_filename=key_file,
        look_for_keys=args.password is None and key_file is None,
    )

    sftp = client.open_sftp()
    with sftp.open(args.remote_script, "w") as remote_file:
        remote_file.write(script_text)
    sftp.close()

    command = build_remote_command(args)

    if args.wait:
        _, stdout, stderr = client.exec_command(command)
        print(stdout.read().decode(errors="replace"), end="")
        err = stderr.read().decode(errors="replace")
        if err:
            print(err, end="")
    else:
        _, stdout, stderr = client.exec_command(command)
        print(stdout.read().decode(errors="replace").strip())
        err = stderr.read().decode(errors="replace").strip()
        if err:
            print(err)

    client.close()


if __name__ == "__main__":
    main()