from django.db.models.expressions import Subquery

EXPAND_UPWARDS_CATEGORY_QUERY = """
(SELECT "CATALOGUE_CATEGORY_JOIN"."id" FROM "catalogue_category" AS "CATALOGUE_CATEGORY_BASE"
LEFT JOIN "catalogue_category" AS "CATALOGUE_CATEGORY_JOIN" ON (
    "CATALOGUE_CATEGORY_BASE"."path" LIKE "CATALOGUE_CATEGORY_JOIN"."path" || '%%%%'
    AND "CATALOGUE_CATEGORY_BASE"."depth" >= "CATALOGUE_CATEGORY_JOIN"."depth"
)
WHERE "CATALOGUE_CATEGORY_BASE"."id" IN (%(subquery)s))
"""


EXPAND_DOWNWARDS_CATEGORY_QUERY = """
(SELECT "CATALOGUE_CATEGORY_JOIN"."id" FROM "catalogue_category" AS "CATALOGUE_CATEGORY_BASE"
LEFT JOIN "catalogue_category" AS "CATALOGUE_CATEGORY_JOIN" ON (
    "CATALOGUE_CATEGORY_JOIN"."path" LIKE "CATALOGUE_CATEGORY_BASE"."path" || '%%%%'
    AND "CATALOGUE_CATEGORY_BASE"."depth" <= "CATALOGUE_CATEGORY_JOIN"."depth"
)
WHERE "CATALOGUE_CATEGORY_BASE"."id" IN (%(subquery)s))
"""


class ExpandUpwardsCategoryQueryset(Subquery):
    template = EXPAND_UPWARDS_CATEGORY_QUERY

    def as_sqlite(self, compiler, connection):
        return super().as_sql(compiler, connection, self.template[1:-1])


class ExpandDownwardsCategoryQueryset(Subquery):
    template = EXPAND_DOWNWARDS_CATEGORY_QUERY

    def as_sqlite(self, compiler, connection):
        return super().as_sql(compiler, connection, self.template[1:-1])
