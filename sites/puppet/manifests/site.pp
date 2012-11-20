# Set default path for all Exec tasks
Exec {
	path => "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
}

class python_dependencies {
	exec {"update-packages":
		command => "apt-get update",
	}
    $packages = [
		"build-essential",
		"python-setuptools",
		"python-imaging",
		"python-memcache",
		"postgresql-server-dev-9.1",
    ]
    package {
        $packages: ensure => installed,
		require => Exec["update-packages"]
    }
}

node precise64 {

	include python_dependencies
	include userconfig

	# Memcached
	class {"memcached": max_memory => 64 }

	# Postgres
	$user = "oscar_user"
	$password = "oscar_password"
	$database_name = "oscar_vagrant"
	class {"postgresql::server": }
	pg_user {$user:
		ensure => present,
		password => $password,
		createdb => true,
		require => Class["postgresql::server"],
	}
	pg_database {$database_name:
		ensure => present,
		owner => $user,
		require => [Pg_user[$user]],
		encoding => "UTF8",
	}

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
	    command => "$virtualenv/bin/python setup.py develop",
		require => Python::Venv::Isolate[$virtualenv]
	}
}
