"""Этап 2. REPL с CLI-параметрами, YAML-конфигом и стартовым скриптом."""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ============================================================
# VFS (упрощённая загрузка — реальная логика на этапе 3)
# ============================================================

@dataclass
class VfsNode:
    """Узел VFS: файл или директория."""

    type: str
    content: str = ""
    owner: str = "user"
    children: dict[str, "VfsNode"] = field(default_factory=dict)


class VirtualFileSystem:
    """Виртуальная файловая система в памяти (упрощённая для этапа 2)."""

    def __init__(self, name: str = "default_vfs", root: VfsNode | None = None) -> None:
        self.name = name
        self.root = root or VfsNode(type="dir")

    @classmethod
    def from_json(cls, path: str) -> "VirtualFileSystem":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("name", Path(path).stem)
        return cls(name=name)


# ============================================================
# Конфигурация
# ============================================================

@dataclass
class Config:
    """Конфигурация эмулятора."""

    vfs_path: str | None = None
    startup_script: str | None = None


def load_config(args: argparse.Namespace) -> Config:
    """Загружает конфиг: CLI + YAML. YAML приоритетнее."""
    cfg = Config(vfs_path=args.vfs, startup_script=args.script)

    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if "vfs_path" in data:
                cfg.vfs_path = data["vfs_path"]
            if "startup_script" in data:
                cfg.startup_script = data["startup_script"]
        except FileNotFoundError:
            print(f"Ошибка: конфиг-файл не найден: {args.config}")
        except yaml.YAMLError as e:
            print(f"Ошибка чтения YAML: {e}")

    return cfg


# ============================================================
# Оболочка
# ============================================================

ENV_PATTERN = re.compile(r"\$(\w+)")


def expand_env(text: str) -> str:
    """Раскрывает переменные окружения реальной ОС."""
    return ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1), ""), text)


def parse_line(line: str) -> tuple[str, list[str]]:
    """Разбирает строку на команду и аргументы."""
    expanded = expand_env(line).strip()
    if not expanded:
        return "", []
    parts = expanded.split()
    return parts[0], parts[1:]


class Shell:
    """Эмулятор командной оболочки."""

    def __init__(self, vfs: VirtualFileSystem) -> None:
        self.vfs = vfs
        self.cwd: list[str] = []
        self.running = True

    def prompt(self) -> str:
        path = "/" + "/".join(self.cwd) if self.cwd else "/"
        return f"{self.vfs.name}:{path}$ "

    # ----- команды-заглушки -----

    def cmd_ls(self, args: list[str]) -> None:
        print(f"ls: {args}")

    def cmd_cd(self, args: list[str]) -> None:
        print(f"cd: {args}")

    def cmd_exit(self, args: list[str]) -> None:
        self.running = False

    # ----- цикл -----

    def execute(self, line: str) -> None:
        command, args = parse_line(line)
        if not command:
            return
        method = getattr(self, f"cmd_{command.replace('-', '_')}", None)
        if method is None:
            print(f"Ошибка: неизвестная команда '{command}'")
            return
        method(args)

    def run_interactive(self) -> None:
        while self.running:
            try:
                line = input(self.prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            self.execute(line)

    def run_script(self, path: str) -> None:
        """Выполняет стартовый скрипт. Останавливается при первой ошибке."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Ошибка: скрипт не найден: {path}")
            return

        for line in lines:
            line = line.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            print(f"{self.prompt()}{line}")
            try:
                self.execute(line)
            except Exception as e:
                print(f"Ошибка выполнения: {e}")
                break
            if not self.running:
                break


# ============================================================
# Точка входа
# ============================================================

def parse_args() -> argparse.Namespace:
    """CLI-параметры."""
    p = argparse.ArgumentParser(description="Эмулятор оболочки ОС")
    p.add_argument("--vfs", help="Путь к JSON-файлу VFS")
    p.add_argument("--script", help="Путь к стартовому скрипту")
    p.add_argument("--config", help="Путь к YAML-конфигу")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args)

    # Отладочный вывод параметров (требование этапа 2)
    print("Параметры запуска:")
    print(f"  VFS: {cfg.vfs_path}")
    print(f"  Script: {cfg.startup_script}")

    if cfg.vfs_path:
        try:
            vfs = VirtualFileSystem.from_json(cfg.vfs_path)
        except FileNotFoundError:
            print(f"Ошибка: файл VFS не найден: {cfg.vfs_path}")
            vfs = VirtualFileSystem()
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка формата VFS: {e}")
            vfs = VirtualFileSystem()
    else:
        vfs = VirtualFileSystem(name="default_vfs")

    shell = Shell(vfs)

    if cfg.startup_script:
        shell.run_script(cfg.startup_script)

    if shell.running:
        shell.run_interactive()


if __name__ == "__main__":
    main()