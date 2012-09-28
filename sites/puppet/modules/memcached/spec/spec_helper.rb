require 'puppet'
require 'rubygems'
require 'rspec-puppet'

# get the value of a certain parameter
def param_value(subject, type, title, param)
  subject.resource(type, title).send(:parameters)[param.to_sym]
end

RSpec.configure do |c|
  c.module_path = File.join(File.dirname(__FILE__), '../../')
  c.manifest_dir = File.expand_path(File.join(File.dirname(__FILE__), 'fixtures/manifests'))
end
