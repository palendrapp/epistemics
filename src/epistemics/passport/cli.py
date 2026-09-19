"""Create, render and check local draft passports without changing source artifacts."""

from pathlib import Path

from epistemics.passport.build import build_passport, verify_derivation
from epistemics.passport.models import read_passport
from epistemics.passport.render import render_html, render_markdown


def add_commands(commands):
    parser = commands.add_parser("passport", help="Create and inspect a local draft passport")
    actions = parser.add_subparsers(dest="passport_command", required=True)
    create = actions.add_parser("create", help="Derive a draft from a completed v1–v3 report")
    create.add_argument("--report", type=Path, required=True)
    create.add_argument("--output", type=Path, default=Path("output/passport"))
    create.add_argument(
        "--response-origin",
        choices=["agent", "synthetic", "unspecified"],
        default="unspecified",
        help="Operator assertion; legacy reports do not record whether responses were synthetic",
    )
    render = actions.add_parser(
        "render", help="Render an existing passport JSON; no provenance check"
    )
    render.add_argument("path", type=Path)
    render.add_argument("--format", choices=["html", "markdown"], default="html")
    render.add_argument("--output", type=Path, required=True)
    verify = actions.add_parser(
        "verify", help="Check exact source bytes and deterministic derivation"
    )
    verify.add_argument("path", type=Path)
    verify.add_argument("--report", type=Path, required=True)


def run(args):
    if args.passport_command == "create":
        passport = build_passport(args.report.read_bytes(), response_origin=args.response_origin)
        # Build every artifact before creating the destination; refuse to overwrite prior results.
        artifacts = {
            "passport.json": passport.model_dump_json(indent=2) + "\n",
            "passport.md": render_markdown(passport),
            "passport.html": render_html(passport),
        }
        args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
        for filename, content in artifacts.items():
            (args.output / filename).write_text(content, encoding="utf-8")
        print(f"Created draft, unsigned passport: {args.output / 'passport.html'}")
        print(
            f"Response origin: {passport.context.response_origin}; exact source: {passport.source.sha256}"
        )
        return
    passport = read_passport(args.path.read_bytes())
    if args.passport_command == "verify":
        verify_derivation(passport, args.report.read_bytes())
        print(
            "Source bytes and deterministic interpretation match. Draft unsigned; execution/origin not verified."
        )
        return
    render = render_html if args.format == "html" else render_markdown
    content = render(passport)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(content)
    print(args.output)
