from django.db.models import sql


class FilteredRelationQuery(sql.Query):
    def table_alias(self, table_name, create=False, filtered_relation=None):
        """
        We must override this freaking method because it creates aliases for
        filtered_relations. This causes the WHERE clauses to become unbound.
        For now this is the fix, but it means the aliases for the filtered_relations
        must be unique over the COMBINED query
        """
        if create and filtered_relation is not None:
            alias_list = self.table_map.get(table_name)
            if alias_list:
                alias = filtered_relation.alias
                alias_list.append(alias)
                self.alias_refcount[alias] = 1
                return alias, True

        return super(FilteredRelationQuery, self).table_alias(table_name, create, filtered_relation)
