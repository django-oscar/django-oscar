=====
Tests
=====

Tests are split into 3 folders:

* unit - These are for tests that exercise a single unit of functionality, like
  a single model.  Ideally, these should not write to the database at all - all
  operations should be in memory.

* integration - These are for tests that exercise a collection or chain of
  units, like testing a template tag.  

* functional - These should be as close to "end-to-end" as possible.  Most of
  these tests should use WebTest to simulate the behaviour of a user browsing
  the site.

The 'integration' folder is relatively new and the process of migrating tests
from 'unit' is in place.