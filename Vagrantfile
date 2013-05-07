# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# Before bringing up your Vagrant machine, run:
#
#     make puppet
#
# to fetch the puppet modules required to build the VM.

Vagrant::Config.run do |config|
    config.vm.box = "precise64"
    config.vm.box_url = "http://files.vagrantup.com/precise64.box"
	config.vm.forward_port 8000, 8080
	config.vm.forward_port 80, 8081
	#config.vm.boot_mode = :gui
    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "sites/puppet/manifests"
        puppet.manifest_file = "site.pp"
        puppet.module_path = "sites/puppet/modules"
		#puppet.options = "--debug"
    end
end
