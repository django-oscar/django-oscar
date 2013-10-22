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
		"libmysqlclient-dev",
		"git-core",
    ]
    package {
        $packages: ensure => installed,
		require => Exec["update-packages"]
    }
}

node precise64 {

	include python_dependencies
	include userconfig

	# Apache
	class {"apache": }
	class {"apache::mod::wsgi": }
	file {"/etc/apache2/sites-enabled/vagrant.conf":
	    source => "/vagrant/sites/sandbox/deploy/apache2/vagrant.conf"
	}

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

	# MySQL
	class {"mysql::bindings::python": }
	class {"mysql::server":
	    override_options => {"root_password" => "root_password"}
	}
	mysql::db {$database_name:
		user => $user,
		password => $password,
		host => "localhost",
		grant => ["all"],
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
	python::pip::requirements {"/vagrant/requirements_vagrant.txt":
	    venv => $virtualenv,
		require => Python::Venv::Isolate[$virtualenv]
	}
    exec {"install-oscar":
	    command => "$virtualenv/bin/python /vagrant/setup.py develop",
		require => Python::Venv::Isolate[$virtualenv]
	}
}
