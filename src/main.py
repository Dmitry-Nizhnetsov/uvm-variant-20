"""Этап 1. REPL — минимальный прототип эмулятора командной оболочки."""
from __future__ import annotations

import os
import re

VFS_NAME = "my_vfs"

ENV_PATTERN = re.compile(r"\$(\w+)")


def expand_env(text: str) -> str:
    """Раскрывает переменные окружения реальной ОС.

    Пример: "$HOME/dir" -> "/Users/username/dir".
    """
    return ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1), ""), text)


def parse_line(line: str) -> tuple[str, list[str]]:
    """Разбирает строку на команду и аргументы."""
    expanded = expand_env(line).strip()
    if not expanded:
        return "", []
    parts = expanded.split()
    return parts[0], parts[1:]


def cmd_ls(args: list[str]) -> None:
    """Заглушка ls — выводит имя и аргументы."""
    print(f"ls: {args}")


def cmd_cd(args: list[str]) -> None:
    """Заглушка cd — выводит имя и аргументы."""
    print(f"cd: {args}")


def prompt() -> str:
    """Приглашение содержит имя VFS."""
    return f"{VFS_NAME}$ "


def execute(line: str) -> bool:
    """Выполняет одну строку. Возвращает False, если нужно выйти."""
    command, args = parse_line(line)

    if not command:
        return True

    if command == "exit":
        print("Выход.")
        return False
    elif command == "ls":
        cmd_ls(args)
    elif command == "cd":
        cmd_cd(args)
    else:
        print(f"Ошибка: неизвестная команда '{command}'")

    return True


def main() -> None:
    """Основной цикл REPL."""
    print(f"Эмулятор запущен. VFS: {VFS_NAME}")
    while True:
        try:
            line = input(prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not execute(line):
            break


if __name__ == "__main__":
    main()