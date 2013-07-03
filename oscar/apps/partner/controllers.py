# -*- coding: utf-8 -*-


class StockRecordController(object):

    def has_stockrecord(self, product):
        return product.stockrecords.count() > 0

    def is_available_to_buy(self, product):
        return any([stockrecord.is_available_to_buy
                    for stockrecord in product.stockrecords.all()])

    def is_purchase_permitted(self, product, user=None, quantity=1):
        for stockrecord in product.stockrecords.all():
            if stockrecord.is_purchase_permitted(user, quantity, self):
                return True, None
        #FIXME Currently just returns error message of primary stock record
        return self.select_stockrecord_for(product).is_purchase_permitted(
            user, quantity, self)


    def select_stockrecord_for(self, product):
        try:
            return product.stockrecords.all()[0]
        except:
            return None
