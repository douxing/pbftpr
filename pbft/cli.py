import binascii
import os
import sys

import click
import coincurve
import toml

@click.group(invoke_without_command=False)
def cli_main():
    pass

@cli_main.command()
@click.option('-n', default = 4)
@click.option('-c', default = 1)
@click.option('--force', '-f', is_flag = True)
@click.argument('outfolder', required = True)
def gen(n, c, force, outfolder):
    try:
        os.mkdir(outfolder)
    except FileExistsError as e:
        if not force:
            print('Folder {} already exist, please add --force to override!'.format(
                outfolder
            ))
            sys.exit(-1)

    print('Going to generate {} nodes and {} clients in {} ...'.format(
        n, c, outfolder
    ))

    _owd = os.getcwd()
    os.chdir(outfolder)

    # generate keys for replica and clients
    for name, count in [('replica', n), ('client', c)]:
        keys = []
        for i in range(count):
            k = coincurve.PrivateKey() 
            keys.append(k)
            with open('{}_{}.txt'.format(name, i), 'w') as f:
                toml.dump({
                    'title': '{} {}'.format(name, i),
                    'private_key': k.to_hex(),
                }, f)
            
        pubkeys = dict()
        pubkeys['title'] = '{} public keys'.format(name)
        pubkeys['keys'] = []
        for k in keys:
            pubkeys['keys'].append({
                'public_key': binascii.b2a_hex(k.public_key.format()).decode()
            })

        with open('{}_public_keys.txt'.format(name), 'w') as f:
            toml.dump(pubkeys, f)
    
    os.chdir(_owd)
    print('Successfully generated!')
    
