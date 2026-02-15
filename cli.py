#!/usr/bin/env python3
import os
import subprocess
import sys
import argparse
import shutil
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

def cleanup_conflicts(package, stow_dir, target_dir):
    """
    Remove files/directories in target_dir that strictly conflict with
    the package contents, allowing stow to proceed.
    """
    package_path = stow_dir / package
    if not package_path.exists():
        return

    # Helper to resolve absolute path safely
    def is_correct_link(link, target):
        try:
            return link.resolve(strict=True) == target.resolve(strict=True)
        except Exception:
            return False

    # Walk top-down
    for root, dirs, files in os.walk(package_path):
        rel_root = Path(root).relative_to(package_path)
        
        # Check directories (source is dir)
        # We only care if target is a FILE (blocking dir creation/traversal)
        for d in dirs:
            rel_path = rel_root / d
            target_path = target_dir / rel_path
            
            # Check if exists (including broken symlinks)
            if target_path.is_symlink() or target_path.exists():
                if not target_path.is_dir():
                    # It's a file (or symlink to file) blocking a directory
                    print(f"  [CLEANUP] Removing file blocking directory: {target_path}")
                    try:
                        target_path.unlink()
                    except OSError as e:
                        print(f"  [WARN] Failed to remove {target_path}: {e}")
        
        # Check files (source is file)
        for f in files:
            rel_path = rel_root / f
            target_path = target_dir / rel_path
            source_file = package_path / rel_path
            
            if target_path.is_symlink():
                # Check where it points
                if not is_correct_link(target_path, source_file):
                    print(f"  [CLEANUP] Replacing symlink: {target_path}")
                    try:
                        target_path.unlink()
                    except OSError as e:
                        print(f"  [WARN] Failed to remove {target_path}: {e}")
            elif target_path.exists():
                 # It's a real file (or dir? if source is file and target is dir)
                 if target_path.is_dir():
                     print(f"  [CLEANUP] Removing directory blocking file: {target_path}")
                     try:
                         shutil.rmtree(target_path)
                     except OSError as e:
                         print(f"  [WARN] Failed to remove {target_path}: {e}")
                 else:
                     print(f"  [CLEANUP] Removing conflicting file: {target_path}")
                     try:
                         target_path.unlink()
                     except OSError as e:
                         print(f"  [WARN] Failed to remove {target_path}: {e}")

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
        
        # Clean up conflicts before stowing
        cleanup_conflicts(package, STOW_DIR, home_dir)

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
