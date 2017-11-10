import binascii
import os
import sys

import click
import coincurve
import toml

from .node import Node
from .replica import Replica
from .client import Client

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

    print('Going to generate {} replicas and {} clients in {} ...'.format(
        n, c, outfolder
    ))

    _owd = os.getcwd()
    os.chdir(outfolder)

    port_index = 25600

    # generate keys for replica and clients
    for name, count in [('replica', n), ('client', c)]:
        keys = []
        for i in range(count):
            k = coincurve.PrivateKey() 
            keys.append(k)
            with open('{}_{}.toml'.format(name, i), 'w') as f:
                toml.dump({
                    'title': '{}_{}'.format(name, i),
                    'node': {
                        'index': i,
                        'type': name,
                        'private_key': k.to_hex(),
                    }
                }, f)
            
        pubkeys = dict()
        pubkeys['title'] = '{}'.format(name)
        pubkeys['nodes_count'] = count
        pubkeys['nodes'] = []
        for i, k in enumerate(keys):
            pubkeys['nodes'].append({
                'index': i,
                'type': name,
                'public_key': binascii.b2a_hex(k.public_key.format()).decode(),
                'ip': '127.0.0.1',
                'port': port_index,
            })
            port_index += 1

        with open('{}_configs.toml'.format(name), 'w') as f:
            toml.dump(pubkeys, f)
    
    os.chdir(_owd)
    print('''Successfully generated!
Go to '{}' and tune parameters in public config files
according to your needs!'''.format(outfolder))

@cli_main.command()
@click.option('--fault_count', '-f')
@click.option('--replica_count', '-n')
@click.option('--client_count', '-c')
@click.argument('replica_configs', type=click.File(mode='r'))
@click.argument('client_configs', type=click.File(mode='r'))
@click.argument('node_config', type=click.File(mode='r'))
def run(replica_count, fault_count, client_count,
        replica_configs, client_configs, node_config):
    try:
        _rcs = toml.loads(replica_configs)
        _ccs = toml.loads(client_configs)
        _nc  = toml.loads(node_config)
    except toml.TomlDecodeError as tde:
        print('toml decode error: {}'.format(tde))
        sys.exit(-1)

    if not _nc['node'] or not isinstance(_nc['node'], dict):
        print("config_config node attribute not exist!")
        sys.exit(-1)

    configs = dict({
        
    })
        
    node = None
    if _nc['node']['type'] == 'replica':
        node = Replica()
    elif _nc['node']['type'] == 'client':
        node = Client()

