import binascii
import math
import os
import sys
import traceback

import click
import rsa
import toml

from .node import Node
from .replica import Replica
from .principal import Principal
from .client import Client

gintervals = dict({
    'auth': 30 * 60 * 1000,
    'status': 150,
    'view_change': 5000,
    'recovery': 90 * 24 * 60 * 60 * 1000,
    'idle': 120 * 1000,
})

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
                d = {
                    'title': '{}_{}'.format(name, i),
                    'node': {
                        'index': i,
                        'type': name,
                        'private_key_file': privkey_fname,
                        'public_key_file': pubkey_fname,
                        'auth_interval': gintervals['auth'],
                    }
                }

                if name == 'replica':
                    # add additional parameters
                    for n in ('status', 'view_change', 'recovery', 'idle'):
                        d['node']['{}_interval'.format(n)] = gintervals[n]

                toml.dump(d, f)

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

def parse_args(replica_count, fault_count, client_count,
               replica_configs, client_configs, node_config):
    """Parse arguments for replica and client
    """

    node = toml.load(node_config)['node']

    with open(node['private_key_file']) as f:
        node['private_key'] = rsa.PrivateKey.load_pkcs1(f.read())
    with open(node['public_key_file']) as f:
        node['public_key'] = rsa.PublicKey.load_pkcs1(f.read())

    replicas = toml.load(replica_configs)['nodes']

    n = replica_count or len(replicas)
    if n > len(replicas):
        raise ValueError

    f = fault_count or (n - 1)// 3

    replica_principals = []
    for i in range(n):
        r = replicas[i]
        with open(r['public_key_file']) as f:
            p = Principal(i, public_key = rsa.PublicKey.load_pkcs1(f.read()),
                          ip = r['ip'], port = r['port'])
            replica_principals.append(p)

    clients = toml.load(client_configs)['nodes']

    client_principals = []
    for i, c in enumerate(clients):
        with open(c['public_key_file']) as f:
            p = Principal(i, public_key = rsa.PublicKey.load_pkcs1(f.read()),
                          ip = c['ip'], port = c['port'])
            client_principals.append(p)

    node['n'] = n
    node['f'] = f
    node['replica_principals'] = replica_principals
    node['client_principals'] = client_principals

    return node

client_keys = {
    'n','f', 'private_key', 'public_key',
    'auth_interval',
    'replica_principals', 'client_principals',
}

@cli_main.command()
@click.option('--fault_count', '-f')
@click.option('--replica_count', '-n')
@click.option('--client_count', '-c')
@click.option('--replica_configs', '-R',
                type=click.File(mode='r'),
                default='replica_configs.toml')
@click.option('--client_configs', '-C',
                type=click.File(mode='r'),
                default='client_configs.toml')
@click.argument('node_config',
                type=click.File(mode='r'))
def client(**kwargs):
    try:
        node_config = parse_args(**kwargs)
        client_config = { k: node_config[k] for k in client_keys }
        node = Client(**client_config)
        node.run()
    except KeyboardInterrupt:
        print('Interrupted by user')
    except:
        traceback.print_exc()
    finally:
        print('client {} exited!'.format(node_config['index']))

    
replica_keys = client_keys.union({
    '{}_interval'.format(name) for name in gintervals
})

@cli_main.command()
@click.option('--fault_count', '-f')
@click.option('--replica_count', '-n')
@click.option('--client_count', '-c')
@click.option('--replica_configs', '-R',
                type=click.File(mode='r'),
                default='replica_configs.toml')
@click.option('--client_configs', '-C',
                type=click.File(mode='r'),
                default='client_configs.toml')
@click.argument('node_config',
                type=click.File(mode='r'))
def replica(**kwargs):
    try:
        node_config = parse_args(**kwargs)
        replica_config = { k: node_config[k] for k in replica_keys }
        node = Replica(**replica_config)
        node.run()
    except KeyboardInterrupt:
        print('Interrupted by user')
    except:
        traceback.print_exc()
    finally:
        print('replica {} exited!'.format(node_config['index']))
