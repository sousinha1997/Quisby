import click
from pquisby.command import process_benchmark, compare_benchmark


@click.group(help="Quisby is .....")
def cli():
    pass


cli.add_command(process_benchmark.process_run)
cli.add_command(compare_benchmark.compare_benchmark)

def main():
    cli()

if __name__ == '__main__':
    main()