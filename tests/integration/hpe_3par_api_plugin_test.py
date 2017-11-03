import docker
import pytest
import yaml

from .base import BaseAPIIntegrationTest, TEST_API_VERSION, BUSYBOX
from ..helpers import requires_api_version
from hpe_3par_manager import HPE3ParBackendVerification,HPE3ParVolumePluginTest

# Importing test data from YAML config file
with open("testdata/test_config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Declaring Global variables and assigning the values from YAML config file
HPE3PAR = cfg['plugin']['latest_version']
HPE3PAR2 = cfg['plugin']['old_version']
HOST_OS = cfg['platform']['os']
CERTS_SOURCE = cfg['plugin']['certs_source']


@requires_api_version('1.25')
class PluginTest(HPE3ParBackendVerification,HPE3ParVolumePluginTest):

    @classmethod
    def teardown_class(cls):
        c = docker.APIClient(
            version=TEST_API_VERSION, timeout=60,
            **docker.utils.kwargs_from_env()
        )
        try:
            c.remove_plugin(HPE3PAR, force=True)
            if HPE3PAR2:
                c.remove_plugin(HPE3PAR2, force=True)
        except docker.errors.APIError:
            pass

    def teardown_method(self, method):
        try:
            self.client.disable_plugin(HPE3PAR)
            if HPE3PAR2:
                self.client.disable_plugin(HPE3PAR2)
        except docker.errors.APIError:
            pass

        for p in self.tmp_plugins:
            try:
                self.client.remove_plugin(p, force=True)
            except docker.errors.APIError:
                pass

    def ensure_plugin_installed(self, plugin_name):
        # This test will ensure if the plugin is installed
        try:
            return self.client.inspect_plugin(plugin_name)
        except docker.errors.NotFound:
            prv = self.client.plugin_privileges(plugin_name)
            for d in self.client.pull_plugin(plugin_name, prv):
                pass
        return self.client.inspect_plugin(plugin_name)

    def test_enable_plugin(self):
        # This test will configure and enable the plugin
        pl_data = self.ensure_plugin_installed(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        if HOST_OS == 'ubuntu':
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE
                })
        else:
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE,
                'glibc_libs.source': '/lib64'
                })
        assert pl_data['Enabled'] is False
        assert self.client.enable_plugin(HPE3PAR)
        pl_data = self.client.inspect_plugin(HPE3PAR)
        assert pl_data['Enabled'] is True
        with pytest.raises(docker.errors.APIError):
            self.client.enable_plugin(HPE3PAR)

    def test_disable_plugin(self):
        # This test will enable and disable the plugin
        pl_data = self.ensure_plugin_installed(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        if HOST_OS == 'ubuntu':
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE
                })
        else:
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE,
                'glibc_libs.source': '/lib64'
                })
        assert pl_data['Enabled'] is False
        assert self.client.enable_plugin(HPE3PAR)
        pl_data = self.client.inspect_plugin(HPE3PAR)
        assert pl_data['Enabled'] is True
        self.client.disable_plugin(HPE3PAR)
        pl_data = self.client.inspect_plugin(HPE3PAR)
        assert pl_data['Enabled'] is False
        with pytest.raises(docker.errors.APIError):
            self.client.disable_plugin(HPE3PAR)

    def test_inspect_plugin(self):
        # This test will inspect the plugin
        self.ensure_plugin_installed(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        data = self.client.inspect_plugin(HPE3PAR)
        assert 'Config' in data
        assert 'Name' in data
        assert data['Name'] == HPE3PAR

    def test_list_plugins(self):
        # This test will list all installed plugin
        self.ensure_plugin_installed(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        data = self.client.plugins()
        assert len(data) > 0
        plugin = [p for p in data if p['Name'] == HPE3PAR][0]
        assert 'Config' in plugin

    def test_remove_plugin(self):
        # This test will remove the plugin
        pl_data = self.ensure_plugin_installed(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        assert pl_data['Enabled'] is False
        assert self.client.remove_plugin(HPE3PAR) is True

    def test_force_remove_plugin(self):
        # This test will remove the plugin forcefully
        self.ensure_plugin_installed(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        if HOST_OS == 'ubuntu':
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE
                })
        else:
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE,
                'glibc_libs.source': '/lib64'
                })
        self.client.enable_plugin(HPE3PAR)
        assert self.client.inspect_plugin(HPE3PAR)['Enabled'] is True
        assert self.client.remove_plugin(HPE3PAR, force=True) is True

    def test_install_plugin(self):
        # This test will remove plugin first if installed, and then install and enable the plugin
        try:
            self.client.remove_plugin(HPE3PAR, force=True)
        except docker.errors.APIError:
            pass

        prv = self.client.plugin_privileges(HPE3PAR)
        self.tmp_plugins.append(HPE3PAR)
        logs = [d for d in self.client.pull_plugin(HPE3PAR, prv)]
        assert filter(lambda x: x['status'] == 'Download complete', logs)
        if HOST_OS == 'ubuntu':
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE
                })
        else:
            self.client.configure_plugin(HPE3PAR, {
                'certs.source': CERTS_SOURCE,
                'glibc_libs.source': '/lib64'
                })
        assert self.client.inspect_plugin(HPE3PAR)
        assert self.client.enable_plugin(HPE3PAR)

    @requires_api_version('1.26')
    def test_upgrade_plugin(self):
        # This test will upgrade the plugin with same repository name
        pl_data = self.ensure_plugin_installed(HPE3PAR2)
        self.tmp_plugins.append(HPE3PAR2)
        self.client.configure_plugin(HPE3PAR2, {
            'certs.source': '/tmp/'
        })
        assert pl_data['Enabled'] is False
        prv = self.client.plugin_privileges(HPE3PAR2)
        logs = [d for d in self.client.upgrade_plugin(HPE3PAR2, HPE3PAR, prv)]
        assert filter(lambda x: x['status'] == 'Download complete', logs)
        if HOST_OS == 'ubuntu':
            self.client.configure_plugin(HPE3PAR2, {
                'certs.source': CERTS_SOURCE
                })
        else:
            self.client.configure_plugin(HPE3PAR2, {
                'certs.source': CERTS_SOURCE,
                'glibc_libs.source': '/lib64'
                })
        assert self.client.inspect_plugin(HPE3PAR2)
        assert self.client.enable_plugin(HPE3PAR2)
        self.client.disable_plugin(HPE3PAR2)
        self.client.remove_plugin(HPE3PAR2, force=True)
