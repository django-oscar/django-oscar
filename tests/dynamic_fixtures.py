from django_dynamic_fixture.ddf import DataFixture
from django_dynamic_fixture.fixture_algorithms.sequential_fixture import \
    SequentialDataFixture

class OscarDynamicDataFixtureClass(SequentialDataFixture):
    """
    This is need to support Oscar's PhoneNumberField: it's a custom type, so we
    must provide values for testing
    """
    def phonenumberfield_config(self, field, key):
        return '+49 351 3296645'
