# Set default path for all Exec tasks
Exec {
	path => "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
}

node precise64 {
	include userconfig

	# Memcached
	class {"memcached": max_memory => 64 }

	# Python
	$virtualenv = "/var/www/virtualenv"
	include python::dev
	include python::venv
	python::venv::isolate { $virtualenv:
	    requirements => "/vagrant/requirements.txt"
	}
    exec {"install-oscar":
	    command => "$virtualenv/bin/python /vagrant/setup.py develop",
		require => Python::Venv::Isolate[$virtualenv]
	}
}
