import click
from commands import single_run,multi_run

@click.group(help="Quisby is .....")
def cli():
    pass

cli.add_command(single_run.single_run)
cli.add_command(multi_run.multi_run)

if __name__ == '__main__':
    cli()
