import tempfile
import docker
import pytest
import yaml

import six

from .base import TEST_API_VERSION, BUSYBOX
from .. import helpers
from ..helpers import requires_api_version
from hpe_3par_manager import HPE3ParBackendVerification,HPE3ParVolumePluginTest

# Importing test data from YAML config file
with open("testdata/test_config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Declaring Global variables and assigning the values from YAML config file
HPE3PAR = cfg['plugin']['latest_version']
HOST_OS = cfg['platform']['os']
CERTS_SOURCE = cfg['plugin']['certs_source']

@requires_api_version('1.20')
class VolumeBindTest(HPE3ParBackendVerification,HPE3ParVolumePluginTest):
    @classmethod
    def setUpClass(cls):
        c = docker.APIClient(
            version=TEST_API_VERSION,
            **docker.utils.kwargs_from_env()
        )
        try:
            prv = c.plugin_privileges(HPE3PAR)
            for d in c.pull_plugin(HPE3PAR, prv):
                pass
            if HOST_OS == 'ubuntu':
                c.configure_plugin(HPE3PAR, {
                    'certs.source': CERTS_SOURCE
                })
            else:
                c.configure_plugin(HPE3PAR, {
                    'certs.source': CERTS_SOURCE,
                    'glibc_libs.source': '/lib64'
                })
            pl_data = c.inspect_plugin(HPE3PAR)
            assert pl_data['Enabled'] is False
            assert c.enable_plugin(HPE3PAR)
            pl_data = c.inspect_plugin(HPE3PAR)
            assert pl_data['Enabled'] is True
        except docker.errors.APIError:
            pass

    @classmethod
    def tearDownClass(cls):
        c = docker.APIClient(
            version=TEST_API_VERSION,
            **docker.utils.kwargs_from_env()
        )
        try:
            c.disable_plugin(HPE3PAR)
        except docker.errors.APIError:
            pass

        try:
            c.remove_plugin(HPE3PAR, force=True)
        except docker.errors.APIError:
            pass

    def test_volume_mount(self):
        '''
           This is a volume mount test.

           Steps:
           1. Create volume and verify if volume got created in docker host and 3PAR array
           2. Create a host config file to setup container.
           3. Create a container and mount volume to it.
           4. Verify if VLUN is available in 3Par array.

        '''
        volume_name = 'volume_mount'
        self.tmp_volumes.append(volume_name)
        self.hpe_create_volume(volume_name, driver=HPE3PAR,
                               size='5', provisioning='thin')
        host_conf = self.hpe_create_host_config(volume_driver=HPE3PAR,
                                                binds='volume_mount:/data1')
        self.hpe_mount_volume(BUSYBOX, command='sh', detach=True,
                              tty=True, stdin_open=True,
                              name='mounter1', host_config=host_conf
                              )
        # Verifying in 3par
        self.hpe_verify_volume_mount(volume_name)

    def test_volume_unmount(self):
        '''
        This is a volume unmount test.

        Steps:
        1. Create volume and verify if volume got created in docker host and 3PAR array
        2. Create a host config file to setup container.
        3. Create a container and perform mount and unmount operation.
        4. Verify if VLUN is removed from 3Par array.

        '''
        volume_name = 'volume_unmount'
        self.tmp_volumes.append(volume_name)
        self.hpe_create_volume(volume_name, driver=HPE3PAR,
                               size='5', provisioning='thin')
        host_conf = self.hpe_create_host_config(volume_driver=HPE3PAR,
                                                binds='volume_unmount:/data1')
        self.hpe_unmount_volume(BUSYBOX, command='sh', detach=True,
                                name='mounter1', tty=True, stdin_open=True,
                                host_config=host_conf
                                )
        # Verifying in 3par
        self.hpe_verify_volume_unmount(volume_name)

    def test_write_and_read_data(self):
        '''
           This is a test of write data and verify that data from file archive of container.

           Steps:
           1. Create volume and verify if volume got created in docker host and 3PAR array
           2. Create a host config file to setup container.
           3. Create a container and mount volume to it.
           4. Write the data in a file which gets created in 3Par volume.
           5. Get the archive of the above file and verify if data is available in that file.

        '''
        client = docker.from_env(version=TEST_API_VERSION)
        volume_name = 'volume_write_read'
        self.tmp_volumes.append(volume_name)
        self.hpe_create_volume(volume_name, driver=HPE3PAR,
                               size='5', provisioning='thin')
        host_conf = self.hpe_create_host_config(volume_driver=HPE3PAR,
                                                binds='volume_write_read:/insidecontainer')
        container = self.hpe_create_container(BUSYBOX, command="sh -c 'echo \"hello\" > /insidecontainer/test'",
                              detach=True, tty=True, stdin_open=True,
                              name='mounter1', host_config=host_conf
                              )
        self.assertIn('Id', container)
        id = container['Id']
        self.tmp_containers.append(id)
        # Mount volume to this container
        self.client.start(id)
        self.client.wait(id)
        out = client.containers.run(
            BUSYBOX, "cat /insidecontainer/test",
            volumes=["volume_write_read:/insidecontainer"]
        )
        self.assertEqual(out, b'hello\n')

    def test_write_data_get_file_archive_from_container(self):
        '''
           This is a test of write data and verify that data from file archive of container.

           Steps:
           1. Create volume and verify if volume got created in docker host and 3PAR array
           2. Create a host config file to setup container.
           3. Create a container and mount volume to it.
           4. Write the data in a file which gets created in 3Par volume.
           5. Get the archive of the above file and verify if data is available in that file.

        '''
        text = 'Python Automation is the only way'
        volume_name = 'data_volume'
        self.tmp_volumes.append(volume_name)
        self.hpe_create_volume(volume_name, driver=HPE3PAR,
                               size='5', provisioning='thin')
        host_conf = self.hpe_create_host_config(volume_driver=HPE3PAR,
                                                binds='data_volume:/vol1')
        ctnr = self.hpe_create_container(BUSYBOX,
                                         command='sh -c "echo {0} > /vol1/file.txt"'.format(text),
                                         tty=True, detach=True, stdin_open=True,
                                         host_config=host_conf
                                         )
        self.client.start(ctnr)
        self.client.wait(ctnr)
        with tempfile.NamedTemporaryFile() as destination:
            strm, stat = self.client.get_archive(ctnr, '/vol1/file.txt')
            for d in strm:
                destination.write(d)
            destination.seek(0)
            retrieved_data = helpers.untar_file(destination, 'file.txt')
            if six.PY3:
                retrieved_data = retrieved_data.decode('utf-8')
            self.assertEqual(text, retrieved_data.strip())

    def test_volume_mount_readonly_fs(self):
        '''
           This is a volume mount test with read-only file system.

           Steps:
           1. Create volume and verify if volume got created in docker host and 3PAR array
           2. Create a host config file to setup container.
           3. Create a container and mount volume to it with command to create a file in 3Par volume.
           4. Verify if container gets exited with 1 exit code just like 'docker wait' command.

        '''
        volume_name = 'volume_readonly'
        self.tmp_volumes.append(volume_name)
        self.hpe_create_volume(volume_name, driver=HPE3PAR,
                               size='5', provisioning='thin')
        host_conf = self.hpe_create_host_config(volume_driver=HPE3PAR,
                                                binds='volume_readonly:/data1:ro')
        ctnr = self.hpe_create_container(BUSYBOX,
                                         command='sh -c "touch /data1/file.txt"',
                                         host_config=host_conf)
        self.client.start(ctnr)
        res = self.client.wait(ctnr)
        self.assertNotEqual(res, 0)
