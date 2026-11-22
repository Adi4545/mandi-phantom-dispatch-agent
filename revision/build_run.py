"""Build the lagged table and evaluate it. Entry point for the revision."""

from revision.build_variant import build
from revision.eval_run import run


def main() -> None:
    build()
    run()


if __name__ == "__main__":
    main()
