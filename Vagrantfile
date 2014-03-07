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
	config.vm.forward_port 8080, 8080
	config.vm.forward_port 80, 8081
	config.vm.forward_port 8082, 8082
	config.vm.forward_port 8083, 8083
	#config.vm.boot_mode = :gui

	# hack to update repos because maikhoepfel can't be asked to learn Puppet to
	# debug the order-of-execution bug in site.pp that causes apt-get to fail
	# to find MySQL packages
	# http://stackoverflow.com/questions/16011294/vagrant-puppet-provisioning-failing
	config.vm.provision :shell, :inline => "apt-get update --fix-missing"

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "sites/puppet/manifests"
        puppet.manifest_file = "site.pp"
        puppet.module_path = "sites/puppet/modules"
		#puppet.options = "--debug"
    end
end
