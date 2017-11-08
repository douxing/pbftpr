import click
import coincurve
import toml
import os

@click.group(invoke_without_command=False)
def cli_main():
    pass

@cli_main.command()
@click.option('-n', default = 4)
@click.option('-c', default = 1)
@click.argument('outfolder', default = 'sample_keys')
def gen(n, c, outfolder):
    try:
        os.makedirs(outfolder, exist_ok = True)
    except OSError as e:
        print('Invalid folder: {}, please check and try again!'.format(
            outfolder
        ))
        os.exit(-1)

    print('Going to generate {} nodes and {} clients in {} ...'.format(
        n, c, outfolder
    ))

    # generate public_keys and private_keys
