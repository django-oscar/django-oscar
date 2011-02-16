import MySQLdb
from decimal import Decimal as D

from django.core.management import setup_environ
import settings as app_settings
setup_environ(app_settings)

from oscar.product.models import ItemClass, Item, AttributeType, ItemAttributeValue, Option
from oscar.stock.models import Partner, StockRecord
from django.db import connection as django_connection

connection = MySQLdb.connect(host='localhost', user='root', passwd='gsiwmm', db='CWDM_app_production_copy')
cursor = connection.cursor(MySQLdb.cursors.DictCursor)


def create_stock_record(product, partner_type, product_id, partner_ref):
    cursor.execute("SELECT * FROM Brd_ProductStock WHERE ProductId = %s", product_id)
    stock_row = cursor.fetchone()
    if stock_row:
        partner,_ = Partner.objects.get_or_create(name="%s (%s)" % (stock_row['Partner'], partner_type))
        price = D(stock_row['Price']) - D(stock_row['PriceSalesTax'])
        print "  - Creating stock record"
        stock_record = StockRecord.objects.create(product=product, partner=partner, partner_reference=partner_ref,
                                                  price_currency='GBP', price_excl_tax=price, 
                                                  num_in_stock=stock_row['NumInStock'])

# Truncate tables
print "Truncating tables"
django_cursor = django_connection.cursor()
django_cursor.execute("set foreign_key_checks=0")
django_cursor.execute("TRUNCATE TABLE product_item")
django_cursor.execute("TRUNCATE TABLE product_attributetype")
django_cursor.execute("TRUNCATE TABLE product_attributevalueoption")
django_cursor.execute("TRUNCATE TABLE product_itemattributevalue")
django_cursor.execute("TRUNCATE TABLE stock_partner")
django_cursor.execute("TRUNCATE TABLE stock_stockrecord")

cursor.execute("SELECT * FROM Brd_ProductsCanonical WHERE Partner = 'Prolog' LIMIT 120")
for row in cursor.fetchall():
    print "Creating canonical product %s" % (row['ProductCode'],)
    pclass,_ = ItemClass.objects.get_or_create(name=row['MediaType'])
    p,_ = Item.objects.get_or_create(title=row['Title'], item_class=pclass, upc=row['ProductCode'])
    
    cursor.execute("SELECT * FROM Brd_Products WHERE CanonicalProductId = %s", row['CanonicalProductId'])
    product_rows = cursor.fetchall()
    if len(product_rows) > 1:
        # Create variant products
        for product_row in product_rows:
            print " - Creating child product %s" % product_row['SourceProductId']
            child_p,_ = Item.objects.get_or_create(parent=p, upc=product_row['SourceProductId'])
            
            # Fetch attributes
            cursor.execute("SELECT VariantType, VariantValue FROM Brd_ProductVariations WHERE ProductId = %s", product_row['ProductId'])
            variant_rows = cursor.fetchall()
            for variant_row in variant_rows:
                print "   - Create attribute %s = %s" % (variant_row['VariantType'], variant_row['VariantValue'])
                attr_type,_ = AttributeType.objects.get_or_create(name=variant_row['VariantType'])
                item_attr_value = ItemAttributeValue.objects.create(product=child_p, type=attr_type, 
                                                                    value=variant_row['VariantValue'])
                if variant_row['VariantType'] == 'CanBePersonalised' and variant_row['VariantValue'] == 'Y':
                    option,_ = Option.objects.get_or_create(name="Personal message")
                    child_p.options.add(option)
                    child_p.save()
            # Stock record for child
            create_stock_record(child_p, row['FulfillmentType'], product_row['ProductId'], product_row['SourceProductId'])
    else:
        # Stand-alone product
        product_row = product_rows[0]
        create_stock_record(p, row['FulfillmentType'], product_row['ProductId'], product_row['SourceProductId'])
    
cursor.close()
print "Finished"