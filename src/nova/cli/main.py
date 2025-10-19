import typer

from nova.cli.command import hello

app = typer.Typer()

app.command()(hello)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
