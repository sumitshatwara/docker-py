import pytest
import docker
import yaml
from .base import TEST_API_VERSION, BUSYBOX
from ..helpers import requires_api_version

from hpe_3par_manager import HPE3ParBackendVerification,HPE3ParVolumePluginTest

# Importing test data from YAML config file
with open("testdata/test_config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Declaring Global variables and assigning the values from YAML config file
HPE3PAR = cfg['plugin']['latest_version']
HOST_OS = cfg['platform']['os']
CERTS_SOURCE = cfg['plugin']['certs_source']
THIN_SIZE = cfg['volumes']['thin_size']
FULL_SIZE = cfg['volumes']['full_size']
DEDUP_SIZE = cfg['volumes']['dedup_size']
COMPRESS_SIZE = cfg['volumes']['compress_size']


@requires_api_version('1.21')
class TestVolumes(HPE3ParBackendVerification,HPE3ParVolumePluginTest):
    @classmethod
    def setUpClass(cls):
        # super(TestVolumes, cls).setUp()
        c = docker.APIClient(
            version=TEST_API_VERSION,
            **docker.utils.kwargs_from_env()
        )
        try:
            prv = c.plugin_privileges(HPE3PAR)
            for d in c.pull_plugin(HPE3PAR, prv):
                pass
            # self.tmp_plugins.append(HPE3PAR)
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
        # super(TestVolumes, cls).tearDown()
        c = docker.APIClient(
            version=TEST_API_VERSION,
            **docker.utils.kwargs_from_env()
        )
        try:
            c.disable_plugin(HPE3PAR)
        except docker.errors.APIError:
            pass

        # for p in self.tmp_plugins:
        try:
            c.remove_plugin(HPE3PAR, force=True)
        except docker.errors.APIError:
            pass

    def test_thin_prov_volume(self):
        '''
           This is a volume create test with provisioning as 'thin'.

           Steps:
           1. Create a volume with provisioning=thin.
           2. Verify if volume and its properties are present in 3Par array.
           3. Inspect this volume.
           4. Delete this volume.
           5. Verify if volume is removed from 3Par array.
        '''
        name = 'Thin_Volume'
        self.tmp_volumes.append(name)
        self.hpe_create_volume(name, driver=HPE3PAR,
                               size=THIN_SIZE, provisioning='thin')
        self.hpe_verify_volume_created(name, size=THIN_SIZE,
                                       provisioning='thin')
        self.hpe_inspect_volume(name, driver=HPE3PAR,
                                size=THIN_SIZE, provisioning='thin')
        self.hpe_delete_volume(name)
        self.hpe_verify_volume_deleted(name)

    def test_full_prov_volume(self):
        '''
           This is a volume create test with provisioning as 'full'.

           Steps:
           1. Create a volume with provisioning=full.
           2. Verify if volume and its properties are present in 3Par array.
           3. Inspect this volume.
           4. Delete this volume.
           5. Verify if volume is removed from 3Par array.
        '''
        name = 'Full_Volume'
        self.tmp_volumes.append(name)
        self.hpe_create_volume(name, driver=HPE3PAR,
                               size=FULL_SIZE, provisioning='full')
        # Verifying in 3par array
        self.hpe_verify_volume_created(name, size=FULL_SIZE,
                                       provisioning='full')
        self.hpe_inspect_volume(name, driver=HPE3PAR,
                                size=FULL_SIZE, provisioning='full')
        self.hpe_delete_volume(name)
        self.hpe_verify_volume_deleted(name)

    def test_flash_cache_volume(self):
        '''
           This is a volume create test with adaptive flash-cache policy.

           Steps:
           1. Create a volume with flash-cache=true.
           2. Verify if volume and its properties are present in 3Par array.
           3. Inspect this volume.
           4. Delete this volume.
           5. Verify if volume is removed from 3Par array.
        '''
        name = 'AFC_Volume'
        self.tmp_volumes.append(name)
        self.hpe_create_volume(name, driver=HPE3PAR,
                               size=THIN_SIZE, flash_cache='true')
        # Verifying in 3par array
        self.hpe_verify_volume_created(name, size=THIN_SIZE,
                                       flash_cache='true')
        self.hpe_inspect_volume(name, driver=HPE3PAR,
                                size=THIN_SIZE, flash_cache='true')
        self.hpe_delete_volume(name)
        self.hpe_verify_volume_deleted(name)

    def test_dedup_prov_volume(self):
        '''
           This is a volume create test with provisioning as 'dedup'.

           Steps:
           1. Create a volume with provisioning=dedup.
           2. Verify if volume and its properties are present in 3Par array.
           3. Inspect this volume.
           4. Delete this volume.
           5. Verify if volume is removed from 3Par array.
        '''
        name = 'Dedup_Volume'
        self.tmp_volumes.append(name)
        self.hpe_create_volume(name, driver=HPE3PAR,
                               size=DEDUP_SIZE, provisioning='dedup')
        # Verifying in 3par array
        self.hpe_verify_volume_created(name, size=DEDUP_SIZE,
                                       provisioning='dedup')
        self.hpe_inspect_volume(name, driver=HPE3PAR,
                                size=DEDUP_SIZE, provisioning='dedup')
        self.hpe_delete_volume(name)
        self.hpe_verify_volume_deleted(name)

    def test_thin_compressed_volume(self):
        '''
           This is a volume create test with provisioning as 'thin' and compression as 'true'.

           Steps:
           1. Create a volume with provisioning=thin and compression=true.
           2. Verify if volume and its properties are present in 3Par array.
           3. Inspect this volume.
           4. Delete this volume.
           5. Verify if volume is removed from 3Par array.
        '''

        name = 'Thin_Compressed_Volume'
        self.tmp_volumes.append(name)
        self.hpe_create_volume(name, driver=HPE3PAR, size=COMPRESS_SIZE,
                               provisioning='thin', compression='true')
        # Verifying in 3par array
        self.hpe_verify_volume_created(name, size=COMPRESS_SIZE,
                                       provisioning='thin', compression='true')
        self.hpe_inspect_volume(name, driver=HPE3PAR, size=COMPRESS_SIZE,
                                provisioning='thin', compression='true')
        self.hpe_delete_volume(name)
        self.hpe_verify_volume_deleted(name)

    def test_dedup_compressed_volume(self):
        '''
           This is a volume create test with provisioning as 'dedup' and compression as 'true'.

           Steps:
           1. Create a volume with provisioning=dedup and compression=true.
           2. Verify if volume and its properties are present in 3Par array.
           3. Inspect this volume.
           4. Delete this volume.
           5. Verify if volume is removed from 3Par array.
        '''
        name = 'Dedup_Compressed_Volume'
        self.tmp_volumes.append(name)
        self.hpe_create_volume(name, driver=HPE3PAR, size=COMPRESS_SIZE,
                               provisioning='dedup', compression='true')
        # Verifying in 3par array
        self.hpe_verify_volume_created(name, size=COMPRESS_SIZE,
                                       provisioning='dedup', compression='true')
        self.hpe_inspect_volume(name, driver=HPE3PAR, size=COMPRESS_SIZE,
                                provisioning='dedup', compression='true')
        self.hpe_delete_volume(name)
        self.hpe_verify_volume_deleted(name)

    def test_list_volumes(self):
        '''
           This is a volume list test.

           Steps:
           1. Create a volume with different volume properties.
           2. Verify if all volumes are present in docker volume list.
        '''
        name = ['vol1', 'vol2', 'vol3']
        for i in range(3):
            self.tmp_volumes.append(name[i])
        volume1 = self.hpe_create_volume(name[0], driver=HPE3PAR)
        volume2 = self.hpe_create_volume(name[1], driver=HPE3PAR,
                                         size=THIN_SIZE, provisioning='thin')
        volume3 = self.hpe_create_volume(name[2], driver=HPE3PAR,
                                         size=THIN_SIZE, flash_cache='true')
        result = self.client.volumes()
        self.assertIn('Volumes', result)
        volumes = result['Volumes']
        volume = [volume1,volume2,volume3]
        for i in range(3):
            self.assertIn(volume[i], volumes)

    @requires_api_version('1.25')
    def test_force_remove_volume(self):
        '''
           This is a remove volumes test with force option.

           Steps:
           1. Create a volume with different volume properties.
           2. Verify if all volumes are removed forcefully.
        '''
        name = ['vol1', 'vol2', 'vol3']
        for i in range(3):
            self.tmp_volumes.append(name[i])
        self.hpe_create_volume(name[0], driver=HPE3PAR)
        self.hpe_create_volume(name[1], driver=HPE3PAR,
                                         size=THIN_SIZE, provisioning='thin')
        self.hpe_create_volume(name[2], driver=HPE3PAR,
                                         size=THIN_SIZE, flash_cache='true')
        for i in range(3):
            self.client.remove_volume(name[i], force=True)

