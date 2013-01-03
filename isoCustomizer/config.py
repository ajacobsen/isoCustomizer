# -*- coding: utf-8 -*-

import os
import glob

from error import SystemError
from configobj import ConfigObj

def write_config(work_path, **options):
    '''Config Datei schreiben'''

    config_dir = os.path.join(work_path, 'config')
    config_file = os.path.join(config_dir, 'config')
    try:
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)

        dirlist = ['local_packages',
                    'packagelists',
                    'binary_includes',
                    'chroot_includes']
        for directory in dirlist:
            if not os.path.exists(os.path.join(config_dir, directory)):
                os.mkdir(os.path.join(config_dir, directory))

    except OSError, detail:
        raise SystemError(detail)	
    
    config = ConfigObj()
    config.filename = config_file
    config['packages'] = options['packages']
    config['volid'] = options['volid'][:32]
    config.write()

    with open(config_file, 'wb') as configfile:
        config.write(configfile)


def read_config(config_dir):
    '''Config Datei lesen'''

    config = ConfigObj(os.path.join(config_dir, 'config'))

    # Packetliste fuer apt erzeugen
    try:
        config['packages'] = [line.strip() for line in config['packages'].split(',')]

        for file in glob.glob('{}/*.list'.format(os.path.join(config_dir, 'packagelists'))):
            with open(file) as packagelist:
                config['packages'] = config['packages'] + [line.strip() for line in packagelist.readlines() if not line.startswith("#")]

        #Paketliste fuer gdebi erzeugen
        config['local_packages'] = glob.glob('{}/*.deb'.format(os.path.join(config_dir, 'local_packages')))

        #includes
        config['binary_includes'] = os.path.join(config_dir, 'binary_includes')
        config['chroot_includes'] = os.path.join(config_dir, 'chroot_includes')
        return config

    except KeyError:
        raise SystemError('./config/config: Datei oder Verzeichnis nicht gefunden.\nWurde \'isoCustomizer config\' schon ausgefuehrt?')

