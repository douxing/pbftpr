import binascii
import math
import os
import sys

import click
import rsa
import toml

from .node import Node
from .replica import Replica
from .principal import Principal
from .client import Client

@click.group(invoke_without_command=False)
def cli_main():
    pass

@cli_main.command()
@click.option('--keysize', default=1024)
@click.option('-n', default = 4)
@click.option('-c', default = 1)
@click.option('--force', '-f', is_flag = True)
@click.argument('outfolder', required = True)
def gen(keysize, n, c, force, outfolder):
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

    # generate keys for replicas and clients
    for name, count in [('replica', n), ('client', c)]:
        pubkeys = []
        for i in range(count):
            (pubkey, privkey) = rsa.newkeys(keysize)
            pubkeys.append(pubkey)

            privkey_fname = '{}_{}.rsa'.format(name, i)
            pubkey_fname = '{}_{}.rsa.pub'.format(name, i)

            with open(privkey_fname, 'w') as f:
                f.write(privkey.save_pkcs1().decode())

            with open(pubkey_fname, 'w') as f:
                f.write(pubkey.save_pkcs1().decode())
            
            with open('{}_{}.toml'.format(name, i), 'w') as f:
                toml.dump({
                    'title': '{}_{}'.format(name, i),
                    'node': {
                        'index': i,
                        'type': name,
                        'private_key_file': privkey_fname,
                        'public_key_file': pubkey_fname,
                    }
                }, f)
                
            
        configs = dict()
        configs['title'] = '{}'.format(name)
        configs['nodes_count'] = count
        configs['nodes'] = []
        for i, k in enumerate(pubkeys):
            configs['nodes'].append({
                'index': i,
                'type': name,
                'public_key_file': '{}_{}.rsa.pub'.format(name, i),
                'ip': '127.0.0.1',
                'port': port_index,
            })
            port_index += 1

        with open('{}_configs.toml'.format(name), 'w') as f:
            toml.dump(configs, f)
    
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
        _rcs = toml.load(replica_configs)
        _ccs = toml.load(client_configs)
        _nc  = toml.load(node_config)
    except toml.TomlDecodeError as tde:
        print('toml decode error: {}'.format(tde))
        sys.exit(-1)

    if 'node' not in _nc or not isinstance(_nc['node'], dict):
        print("node_config 'node' attribute not exist!")
        sys.exit(-1)

    if 'type' not in _nc['node']:
        print("node_config 'node' should have 'type'!")
        sys.exit(-1)
    else:
        node_type = _nc['node']['type']
        
    if 'private_key_file' not in _nc['node']:
        print("node_config 'node' should have 'private_key_file'!")
        sys.exit(-1)
    else:
        with open(_nc['node']['private_key_file']) as f:
            private_key = rsa.PrivateKey.load_pkcs1(f.read())

    if 'public_key_file' not in _nc['node']:
        print("node_config 'node' should have 'public_key_file'!")
        sys.exit(-1)
    else:
        with open(_nc['node']['public_key_file']) as f:
            public_key =  rsa.PublicKey.load_pkcs1(f.read())

    # genrate principals for replicas and clients
    replica_principals = []
    for index, r in enumerate(_rcs['nodes']):
        with open(r['public_key_file']) as f:
            p = Principal(index,
                          public_key = rsa.PublicKey.load_pkcs1(f.read()),
                          ip = r['ip'], port = r['port'])
            replica_principals.append(p)
        
    client_principals = []
    for index, c in enumerate(_ccs['nodes']):
        with open(r['public_key_file']) as f:        
            p = Principal(index,
                          public_key = rsa.PublicKey.load_pkcs1(f.read()),
                          ip = r['ip'], port = r['port'])
            client_principals.append(p)

    n = replica_count or len(replica_principals)
    f = fault_count or n // 3

    kwargs = dict({
        'n': n,
        'f': f,
        'private_key': private_key,
        'public_key': public_key,
        'replica_principals': replica_principals,
        'client_principals': client_principals,
    })

    if node_type == 'replica':
        node = Replica(**kwargs)
    elif node_type == 'client':
        node = Client(**kwargs)
    else:
        print("unknown 'node' 'type': {} {}!".format(node_type, type(node_type)))
        sys.exit(-1)

    try:
        node.run()
    except KeyboardInterrupt:
        print('Interrupted by user')
    except SystemExit as exc:
        print('Interrupted by system exit: {}'.format(exc))
    finally:
        print('process exited!')
