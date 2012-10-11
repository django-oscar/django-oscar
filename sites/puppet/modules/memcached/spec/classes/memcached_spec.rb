require 'spec_helper'
describe 'memcached' do

  let :default_params do
    {
      :package_ensure  => 'present',
      :logfile         => '/var/log/memcached.log',
      :max_memory      => false,
      :listen_ip       => '0.0.0.0',
      :tcp_port        => '11211',
      :udp_port        => '11211',
      :user            => 'nobody',
      :max_connections => '8192'
    }
  end

  [ {},
    {
      :package_ensure  => 'latest',
      :logfile         => '/var/log/memcached.log',
      :max_memory      => '2',
      :listen_ip       => '127.0.0.1',
      :tcp_port        => '11212',
      :udp_port        => '11213',
      :user            => 'somebdy',
      :max_connections => '8193'
    }
  ].each do |param_set|
    describe "when #{param_set == {} ? "using default" : "specifying"} class parameters" do

      let :param_hash do
        default_params.merge(param_set)
      end

      let :params do
        param_set
      end

      ['Debian'].each do |osfamily|

        let :facts do
          {
            :osfamily => osfamily,
            :memorysize => '1',
            :processorcount => '1',
          }
        end

        describe "on supported osfamily: #{osfamily}" do

          it { should contain_class('memcached::params') }

          it { should contain_package('memcached').with_ensure(param_hash[:package_ensure]) }

          it { should contain_file('/etc/memcached.conf').with(
            'owner'   => 'root',
            'group'   => 'root'
          )}

          it { should contain_service('memcached').with(
            'ensure'     => 'running',
            'enable'     => true,
            'hasrestart' => true,
            'hasstatus'  => false
          )}

          it 'should compile the template based on the class parameters' do
            content = param_value(
              subject,
              'file',
              '/etc/memcached.conf',
              'content'
            )
            expected_lines = [
              "logfile #{param_hash[:logfile]}",
              "-l #{param_hash[:listen_ip]}",
              "-p #{param_hash[:tcp_port]}",
              "-U #{param_hash[:udp_port]}",
              "-u #{param_hash[:user]}",
              "-c #{param_hash[:max_connections]}",
              "-t #{facts[:processorcount]}"
            ]
            if(param_hash[:max_memory])
              expected_lines.push("-m #{param_hash[:max_memory]}")
            else
              expected_lines.push("-m #{((facts[:memorysize].to_f*1024)*0.95).floor}")
            end
            (content.split("\n") & expected_lines).should =~ expected_lines
          end
        end
      end
      ['Redhat'].each do |osfamily|
        describe 'on supported platform' do
          it 'should fail' do

          end
        end
      end
    end
  end
end
