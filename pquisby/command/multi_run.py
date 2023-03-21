import click

@click.command()
@click.option('--docker', is_flag=True, help='Indicates the project should be built into docker image')
def multi_run(docker):
    if docker:
        print(f'Building this repo into a docker image...')
    else:
        print(f'Building this repo using default method...')
