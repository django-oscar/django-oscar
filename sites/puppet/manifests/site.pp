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

	# Dev server on port 8080
	exec { "dev-server":
	  command => "bash -c \"source /var/www/virtualenv/bin/activate && /vagrant/sites/sandbox/manage.py runserver 0.0.0.0:8080 &\"",
    }

	# Apache serving WSGI on port 80 (would prefer 8081)
	class {"apache": }
	class {"apache::mod::wsgi": }
	file {"/etc/apache2/sites-enabled/vagrant.conf":
	    source => "/vagrant/sites/puppet/files/apache.conf"
	}

	# gunicorn serving WSGI on unix socket
	class { "python::gunicorn": owner => "root", group => "root" }
	python::gunicorn::instance { "oscar":
	  venv => "/var/www/virtualenv",
	  django => true,
	  src => "/vagrant/sites/sandbox",
    }

	# Nginx in front of Apache (port 8082)
	class { "nginx": }
	nginx::resource::vhost { 'apache_rp':
	  ensure => present,
	  listen_port => 8082,
	}
	nginx::resource::location { 'apache-root':
	  ensure => present,
	  vhost => 'apache_rp',
	  location => '/',
	  proxy => 'http://localhost',
	  proxy_set_headers => {
	  'REMOTE_ADDR' => '$remote_addr',
	  'HTTP_HOST' => '$http_host',
	  },
	}

	# Nginx in front of gunicorn (port 8083)
	nginx::resource::vhost { 'gunicorn_rp':
	  ensure => present,
	  listen_port => 8083,
	}
	nginx::resource::location { 'gunicorn-root':
	  ensure => present,
	  vhost => 'gunicorn_rp',
	  location => '/',
	  proxy => 'http://app1',
	  proxy_set_headers => {
	  'REMOTE_ADDR' => '$remote_addr',
	  'HTTP_HOST' => '$http_host',
	  },
	}
	nginx::resource::upstream { 'app1':
       ensure => present,
       members => [
       'unix:/run/gunicorn/oscar.sock weight=10',
       ],
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
	class {"mysql::bindings": }
	class {"mysql::server":
	    override_options => {"root_password" => "root_password"},
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
	python::pip::requirements {"/vagrant/requirements_less.txt":
	    venv => $virtualenv,
		require => Python::Venv::Isolate[$virtualenv]
	}
    exec {"install-oscar":
	    command => "$virtualenv/bin/python /vagrant/setup.py develop",
		require => Python::Venv::Isolate[$virtualenv]
	}
}
