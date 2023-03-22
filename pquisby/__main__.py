import click
from pquisby.command import single_run, compare_benchmark


@click.group(help="Quisby is .....")
def cli():
    pass


cli.add_command(single_run.single_run)
cli.add_command(compare_benchmark.compare_benchmark)

if __name__ == '__main__':
    cli()
