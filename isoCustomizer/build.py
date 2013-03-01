# -*- coding: utf-8 -*-

import os

import logging

from error import SystemError


def build(work_path, filename, config):
    module_logger = logging.getLogger('isoCustomizer.build')
    module_logger.info('Started building {}'.format(filename))
    module_logger.warning('Warning, exception ahead!')
    raise SystemError('exit')

    squash_fs = os.path.join(work_path, '.build/new_squashfs')
    iso_dir = os.path.join(work_path, '.build/new_iso')

    for e in [squash_fs, iso_dir]:
        if not os.path.exists(e):
            raise OSError('Run extract first')

    set_up_chroot(squash_fs)
    if os.system('LANG=C chroot "{}" /bin/bash -c "apt-get update"'.format(squash_fs)) != 0:
        raise SystemError('Oops! apt-get update fehlgeschlagen.')
    if os.system('LANG=C chroot "{}" /bin/bash -c "apt-get --yes install {}"'.format(squash_fs, ' '.join(config['packages']))) != 0:
        raise SystemError('Oops! apt-get install fehlgeschlagen.')
    os.system('LANG=C chroot "{}" /bin/bash'.format(squash_fs))
    on_exit_chroot(squash_fs)

    if os.system('rsync -at "{}/" "{}"'.format(config['chroot_includes'], squash_fs)) != 0:
        raise SystemError('Oops!')
    if os.system('rsync -at "{}/" "{}"'.format(config['binary_includes'], iso_dir)) != 0:
        raise SystemError('Oops!')

    manifest = os.path.join(iso_dir, 'casper/filesystem.manifest')
    command = "chroot {} dpkg-query -W --showformat='${{Package}} ${{Version}}\n' > {}".format(squash_fs, manifest)
    if os.system(command) != 0:
        raise SystemError('Oops! Erstellen der filesystem.manifest fehlgeschlagen.')
    if os.system('cp -f {0} {0}-desktop'.format(manifest)) != 0:
        raise SystemError('Oops! Erstellen der filesystem.manifest fehlgeschlagen.')
    if os.system("sed -i '/ubiquity\|casper\|gparted\|libdebian-installer4\|user-setup/d' {}-desktop".format(manifest)) != 0:
        raise SystemError('Oops! Erstellen der filesystem.manifest fehlgeschlagen.')

    if os.path.exists(os.path.join(iso_dir, 'casper/filesystem.squashfs')):
        if os.system('rm -f {}'.format(os.path.join(iso_dir, 'casper/filesystem.squashfs'))) != 0:
            raise SystemError('Oops! Das sollte nie passieren.')

    retval = os.system('mksquashfs \
                    \"{0}\" \
                    \"{1}\" \
                    -comp xz \
                    -no-progress'.format(
                                        squash_fs, 
                                        os.path.join(iso_dir, 'casper/filesystem.squashfs')))
    if retval != 0:
        raise SystemError('Oops! Erstellen der filesystem.squashfs fehlgeschlagen.')


    command = 'find {0} -not -name md5sum.txt -and -not -name boot.cat -and -not -name isolinux.bin -type f -print0 | xargs -0 md5sum > {0}/md5sum.txt'.format(iso_dir)
    if os.system(command) != 0:
        raise SystemError('Oops! Erstellen der md5sum.txt fehlgeschlagen.')

    if os.path.isfile('/usr/bin/genisoimage'):
        isotool = 'genisoimage'
    else:
        isotool = 'mkisofs'
    retval = os.system('{} \
                        -o \"{}\" \
                        -b \"isolinux/isolinux.bin\" \
                        -c \"isolinux/boot.cat\" \
                        -no-emul-boot \
                        -boot-load-size 4 \
                        -boot-info-table -V \"{}\" \
                        -cache-inodes \
                        -r \
                        -J \
                        -l \
                        \"{}\"'.format(
                            isotool,
                            filename,
                            config['volid'],
                            iso_dir))
    if retval != 0:
        raise SystemError('Oops! Erstellen der ISO fehlgeschlagen.')

def set_up_chroot(root_path):
    if os.path.exists(os.path.join(root_path, 'etc/resolv.conf')):
        os.system('mv {} {}'.format(os.path.join(root_path, 'etc/resolv.conf'), os.path.join(root_path, 'etc/resolv.conf.bak')))

    os.system('cp -fv /etc/resolv.conf "{}"'.format(os.path.join(root_path, 'etc/')))

    mntlst = ['proc', 'sys', 'dev', 'dev/pts', 'var/run/dbus']
    for entry in mntlst:
        mountpoint = os.path.join(root_path, entry)
        if os.system('mount -o bind {} {}'.format(os.path.join('/', entry), mountpoint)) != 0:
            raise SystemError('Oops! Failed to set up chroot.')
    
    mountpoint = os.path.join(root_path, 'var/lib/dbus/')
    if os.system('mount -o bind {} {}'.format('/var/run/dbus', mountpoint)) != 0:
        raise SystemError('Oops! Failed to set up chroot.')

def on_exit_chroot(root_path):
    os.system('rm -f {}'.format(os.path.join(root_path, 'etc/resolv.conf')))
    if os.path.exists(os.path.join(root_path, 'etc/resolv.conf.bak')):
        os.system('mv {} {}'.format(os.path.join(root_path, 'etc/resolv.conf.bak', os.path.join(root_path, 'etc/resolv.conf'))))
    os.system('LANG=C chroot {} /bin/bash -c "apt-get clean"'.format(root_path))
    os.system('LANG=C chroot {} /bin/bash -c "rm -rf /tmp/*"'.format(root_path))
    os.system('LANG=C chroot {} /bin/bash -c "rm /root/.bash_history"'.format(root_path))
    for root,dirs,files in os.walk(root_path):
        if os.path.ismount(root):
            if os.system('umount -lf {}'.format(root)) != 0:
                raise SystemError('Oops! Failed to exit chroot.')
