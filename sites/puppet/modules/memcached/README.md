
# puppet-memcached

Manage memcached via Puppet

## How to use

### Use roughly 90% of memory

```
    class { 'memcached': }
```

### Set a fixed memory limit in MB

```
    class { 'memcached':
      max_memory => 2048
    }
```

### Other class parameters

* $logfile = '/var/log/memcached.log'
* $listen_ip = '0.0.0.0'
* $tcp_port = 11211
* $udp_port = 11211
* $user = '' (OS specific setting, see params.pp)
* $max_connections = 8192
