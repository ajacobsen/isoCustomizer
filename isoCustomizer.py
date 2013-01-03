#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

# sub-command functions
def config(args):
    '''Erstellen der Config-Datei und der Config-Verzeichnisse'''
    from isoCustomizer.config import write_config
    try:
        write_config(args.work_path, packages=args.packages, volid=args.volid)
    except Exception, detail:
        print detail

def extract(args):
    '''Entpacken der ISO und SquashFS'''
    if os.getuid() != 0:
        os.sys.exit('You must be root')
    from isoCustomizer.extract import extract
    try:
        extract(args.work_path, filename=args.FILENAME)
    except Exception, detail:
        print detail

def build(args):
    '''Erstellen des SquashFS und der ISO'''
    if os.getuid() != 0:
        os.sys.exit('You must be root')
    from isoCustomizer.build import build
    from isoCustomizer.config import read_config
    try:
        config = read_config(os.path.join(args.work_path, 'config'))
        build(args.work_path, args.FILENAME, config)
        print '\n***** Done! *****\n'
    except Exception, detail:
        print detail
    finally:
        for root,dirs,files in os.walk(os.path.join(args.work_path, '.build')):
            if os.path.ismount(root):
                os.system('umount -lf {}'.format(root))

def clean(args):
    '''Aufraeumen'''
    if os.getuid() != 0:
        os.sys.exit('You must be root')
    from isoCustomizer.clean import clean_up
    try:
        clean_up(args.work_path, args.config, args.build)
    except Exception, detail:
        print detail

parser = argparse.ArgumentParser(prog='isoCustomizer')
subparsers = parser.add_subparsers()

parser_config = subparsers.add_parser('config', help='Erstellt ein neues Konfigurationsverzeichnis')
parser_config.add_argument('--packages', type=str, default='', help='Kommagetrennte Paketliste')
parser_config.add_argument('--volid', type=str, default='', help='Volume ID der ISO-Datei')
parser_config.set_defaults(func=config, work_path=os.getcwd())

parser_extract = subparsers.add_parser('extract', help='Entpackt die angegebene ISO-Datei')
parser_extract.add_argument('FILENAME', help='Dateiname der ISO-Datei')
parser_extract.set_defaults(func=extract, work_path=os.getcwd())

parser_build = subparsers.add_parser('build', help='Erstellt eine neue ISO-Datei')
parser_build.add_argument('FILENAME', help='Name der neuen ISO-Datei')
parser_build.set_defaults(func=build, work_path=os.getcwd())


help='''Entfernt temporäre Daten und stellt sicher, 
dass keine Dateisysteme mehr unterhalb des 
Arbeitsverzeichnisses eingebunden sind.'''
parser_clean = subparsers.add_parser('clean', help=help)
parser_clean.add_argument('--config', action='store_true', 
                        help='Wird diese Option gesetzt, wird das Konfigurationsverzeichnis (config) gelöscht')
parser_clean.add_argument('--build', action='store_false',
                        help='Wird diese Option NICHT gesetzt, wird das build-Verzeichnis (.build) gelöscht' )
parser_clean.set_defaults(func=clean, work_path=os.getcwd())

args = parser.parse_args()
args.func(args)
