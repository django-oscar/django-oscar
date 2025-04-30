from django.db.models.expressions import Subquery


# pylint: disable=abstract-method
class ExpandUpwardsCategoryQueryset(Subquery):
    def __init__(self, queryset, **kwargs):
        self.queryset = queryset
        super().__init__(queryset, **kwargs)

    def as_sql(self, compiler, connection, template=None, **extra_context):
        inner_sql, inner_params = compiler.compile(self.queryset.query)

        sql = f"""
        (WITH RECURSIVE category_hierarchy AS (
            SELECT "id", "path", "depth" FROM "catalogue_category" WHERE "id" IN ({inner_sql})
            UNION ALL
            SELECT "parent"."id", "parent"."path", "parent"."depth"
            FROM "catalogue_category" AS "parent"
            JOIN category_hierarchy AS "child" ON (
                "child"."path" LIKE "parent"."path" || '%%'
                AND "parent"."depth" < "child"."depth"
            )
        )
        SELECT DISTINCT "id" FROM category_hierarchy)
        """
        return sql, inner_params

    def as_sqlite(self, compiler, connection):
        sql, params = self.as_sql(compiler, connection)
        return sql[1:-1], params


# pylint: disable=abstract-method
class ExpandDownwardsCategoryQueryset(Subquery):
    def __init__(self, queryset, **kwargs):
        self.queryset = queryset
        super().__init__(queryset, **kwargs)

    def as_sql(self, compiler, connection, template=None, **extra_context):
        inner_sql, inner_params = compiler.compile(self.queryset.query)

        sql = f"""
        (WITH RECURSIVE category_hierarchy AS (
            SELECT "id", "path", "depth" FROM "catalogue_category" WHERE "id" IN ({inner_sql})
            UNION ALL
            SELECT "child"."id", "child"."path", "child"."depth"
            FROM "catalogue_category" AS "child"
            JOIN category_hierarchy AS "parent" ON (
                "child"."path" LIKE "parent"."path" || '%%'
                AND "child"."depth" > "parent"."depth"
            )
        )
        SELECT DISTINCT "id" FROM category_hierarchy)
        """
        return sql, inner_params

    def as_sqlite(self, compiler, connection):
        sql, params = self.as_sql(compiler, connection)
        return sql[1:-1], params
