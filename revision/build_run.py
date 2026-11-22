"""Full leak-free build, evaluation, sensitivity, A10, A18, and figure entry point for Revision v5."""

from revision.build_hp_apple_lagged import build_hp_apple
from revision.build_variant import build
from revision.eval_a10 import run as run_a10
from revision.eval_a18 import run as run_a18
from revision.eval_run import run as run_eval
from revision.make_figures import make_all_figures
from revision.sensitivity_a8 import run as run_sensitivity


def main() -> None:
    build()
    build_hp_apple()
    run_eval()
    run_sensitivity()
    run_a10()
    run_a18()
    make_all_figures()


if __name__ == "__main__":
    main()
