"""Full leak-free build and evaluation entry point for MandiGuard Revision v4."""

from revision.build_hp_apple_lagged import build_hp_apple
from revision.build_variant import build
from revision.eval_run import run as run_eval
from revision.sensitivity_a8 import run as run_sensitivity


def main() -> None:
    build()
    build_hp_apple()
    run_eval()
    run_sensitivity()


if __name__ == "__main__":
    main()
