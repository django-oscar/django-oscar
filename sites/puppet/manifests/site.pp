# Set default path for all Exec tasks
Exec {
	path => "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
}

node precise64 {
	include userconfig

	# Memcached
	class {"memcached": max_memory => 64 }

	# Python
	# - set-up a virtualenv
	# - install testing requirements
	# - install oscar in 'develop' mode
	$virtualenv = "/var/www/virtualenv"
	include python::dev
	include python::venv
	python::venv::isolate { $virtualenv:
	    requirements => "/vagrant/requirements.txt"
	}
    exec {"install-oscar":
	    command => "cd /vagrant && $virtualenv/bin/python setup.py develop",
		require => Python::Venv::Isolate[$virtualenv]
	}
}
