#!/usr/bin/env python3
import os
import subprocess
import sys
import argparse
from pathlib import Path

STOW_DIR = Path("/usr/share/noctyra/stow")

def hello_world(args):
    print(f"Hello, {args.name}!")

def check_stow_installed():
    if not STOW_DIR.exists():
        print(f"Error: Dotfiles not installed in {STOW_DIR}")
        print("Please verify that the noctyra-dotfiles package is installed.")
        return False
    return True

def get_stow_packages():
    if not STOW_DIR.exists():
        return []
    return [d.name for d in STOW_DIR.iterdir() if d.is_dir()]

def install(args):
    if not check_stow_installed():
        return

    packages = get_stow_packages()
    if not packages:
        print("No packages found in stow directory.")
        return

    print(f"Found packages: {', '.join(packages)}")
    home_dir = Path.home()
    
    success_count = 0
    for package in packages:
        print(f"Installing {package}...")
        try:
            # -t: target directory (home)
            # -d: stow directory (/usr/share/noctyra/stow)
            # --restow: unstow then stow again, ensures links are refreshed
            subprocess.run(
                ["stow", "-t", str(home_dir), "-d", str(STOW_DIR), "--restow", package],
                check=True
            )
            print(f"  [OK] {package}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  [FAIL] {package}: {e}")
        except FileNotFoundError:
            print(f"  [ERROR] stow command not found. Please install GNU Stow.")
            return
    
    print(f"\nInstalled {success_count}/{len(packages)} packages.")

def uninstall(args):
    if not check_stow_installed():
        return

    packages = get_stow_packages()
    if not packages:
        print("No packages found to uninstall.")
        return

    print(f"Uninstalling packages: {', '.join(packages)}")
    home_dir = Path.home()

    success_count = 0
    for package in packages:
        print(f"Uninstalling {package}...")
        try:
            subprocess.run(
                ["stow", "-t", str(home_dir), "-d", str(STOW_DIR), "-D", package],
                check=True
            )
            print(f"  [OK] {package}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  [FAIL] {package}: {e}")
        except FileNotFoundError:
            print(f"  [ERROR] stow command not found. Please install GNU Stow.")
            return

    print(f"\nUninstalled {success_count}/{len(packages)} packages.")

def main():
    parser = argparse.ArgumentParser(description="A basic Python CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Command: hello
    # Usage: python cli.py hello --name <name>
    params = subparsers.add_parser('hello', help='Prints Hello World')
    params.add_argument('--name', type=str, default='World', help='Name to greet')
    params.set_defaults(func=hello_world)

    # Command: install
    install_parser = subparsers.add_parser('install', help='Install dotfiles using stow')
    install_parser.set_defaults(func=install)

    # Command: uninstall
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall dotfiles using stow')
    uninstall_parser.set_defaults(func=uninstall)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
